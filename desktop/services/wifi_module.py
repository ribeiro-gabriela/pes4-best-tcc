from typing import Any, List
import pywifi
from pywifi import const
import time
import traceback
import threading
from tftpy import TftpClient

import sys, subprocess, tempfile, os

from data.classes import Connection, Package, Request, Response
from data.errors import RequestTimeoutError, ConnectionAuthenticationError

class WifiModule:
    _tftp_client: TftpClient | None = None

    def __init__(self):
        self.wifi = pywifi.PyWiFi()
        self.iface = self.wifi.interfaces()[0]  
        self.lock = threading.Lock() 

    def scan(self) -> List[dict]: 
        networks = []
        try:
            with self.lock: 
                self.iface.scan()
                time.sleep(2) 
                scan_results = self.iface.scan_results()

            for profile in scan_results:
                ssid = profile.ssid
                signal = profile.signal
                security_type = "Unknown"
                
                if not ssid:
                    continue

                if profile.akm:
                    if const.AKM_TYPE_WPA2PSK in profile.akm:
                        security_type = "WPA2"
                    elif const.AKM_TYPE_WPAPSK in profile.akm:
                        security_type = "WPA"
                    elif const.AKM_TYPE_WPA2 in profile.akm:
                        security_type = "WPA2-Enterprise"
                    elif const.AKM_TYPE_WPA in profile.akm:
                        security_type = "WPA-Enterprise"
                    else:
                        security_type = "Open/Other"
                else:
                    security_type = "Open"
                
                existing_network = next((net for net in networks if net['ssid'] == ssid), None)
                if existing_network:
                    existing_signal_int = int(existing_network['info']['signal'].split(' ')[0]) if 'dBm' in existing_network['info']['signal'] else -100
                    if signal > existing_signal_int:
                        existing_network['info']['signal'] = f"{signal} dBm"
                else:
                    networks.append({"ssid": ssid, "info":{"signal": f"{signal} dBm", "security": security_type}})
                     
        except Exception as e:
            print(f"Error scanning for WiFi networks: {traceback.format_exc()}")
            return [{"ssid": "Scan Error", "info":{"signal": "N/A", "security": str(e)}}]
            
        networks.sort(key=lambda x: int(x['info']['signal'].split(' ')[0]) if 'dBm' in x['info']['signal'] else -100, reverse=True)
        
        return networks


    def _current_ssid_windows(self) -> str | None:
            try:
                out = subprocess.check_output(
                    ["netsh", "wlan", "show", "interfaces"],
                    encoding="utf-8", errors="ignore"
                )
                for line in out.splitlines():
                    s = line.strip()
                    if s.lower().startswith("ssid") and ":" in s:
                        _, val = s.split(":", 1)
                        ssid = val.strip()
                        if ssid and ssid.lower() != "<unknown>":
                            return ssid
            except Exception:
                pass
            return None

    def _win_fallback_connect(self, iface_name: str, ssid: str, password: str | None, wpa2: bool = True):
        if password:
            auth = "WPA2PSK" if wpa2 else "WPAPSK"
            enc  = "AES" if wpa2 else "TKIP"
            xml = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
<name>{ssid}</name>
<SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>
<connectionType>ESS</connectionType>
<connectionMode>auto</connectionMode>
<MSM>
    <security>
    <authEncryption>
        <authentication>{auth}</authentication>
        <encryption>{enc}</encryption>
        <useOneX>false</useOneX>
    </authEncryption>
    <sharedKey>
        <keyType>passPhrase</keyType>
        <protected>false</protected>
        <keyMaterial>{password}</keyMaterial>
    </sharedKey>
    </security>
</MSM>
</WLANProfile>'''
        else:
            xml = f'''<?xml version="1.0"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
<name>{ssid}</name>
<SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>
<connectionType>ESS</connectionType>
<connectionMode>auto</connectionMode>
<MSM>
    <security>
    <authEncryption>
        <authentication>open</authentication>
        <encryption>none</encryption>
        <useOneX>false</useOneX>
    </authEncryption>
    </security>
</MSM>
</WLANProfile>'''

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".xml", encoding="utf-8") as f:
            f.write(xml)
            xml_path = f.name

        try:
            subprocess.check_call(["netsh", "wlan", "add", "profile", f'filename="{xml_path}"', f'interface="{iface_name}"'])
            subprocess.check_call(["netsh", "wlan", "connect", f'name="{ssid}"', f'ssid="{ssid}"', f'interface="{iface_name}"'])
        finally:
            try:
                os.remove(xml_path)
            except Exception:
                pass

        t0 = time.time()
        while time.time() - t0 < 30:
            cur = self._current_ssid_windows()
            if cur == ssid:
                return True
            time.sleep(0.5)
        return False

    def connect(self, target: str, password: str|None = None) -> Connection:
        print(f"Attempting to connect to {target}" + (f" with password: {'*' * len(password)}" if password else " (no password)"))

        with self.lock:
            self.iface.scan()
        time.sleep(2)
        with self.lock:
            scan_results = self.iface.scan_results()

        found_profile = next((p for p in scan_results if p.ssid == target), None)

        profile = pywifi.Profile()
        profile.ssid = target
        profile.auth = const.AUTH_ALG_OPEN
        profile.akm = []
        profile.cipher = const.CIPHER_TYPE_NONE

        def is_psk(p):
            return p and (const.AKM_TYPE_WPA2PSK in p.akm or const.AKM_TYPE_WPAPSK in p.akm)
        def is_open(p):
            return p and (const.AKM_TYPE_NONE in p.akm)

        if is_psk(found_profile):
            if not password:
                raise ConnectionAuthenticationError(f"Network '{target}' requires a password (WPA/WPA2-PSK).")
            if const.AKM_TYPE_WPA2PSK in found_profile.akm:
                profile.akm = [const.AKM_TYPE_WPA2PSK]
                profile.cipher = const.CIPHER_TYPE_CCMP
            elif const.AKM_TYPE_WPAPSK in found_profile.akm:
                profile.akm = [const.AKM_TYPE_WPAPSK]
                profile.cipher = const.CIPHER_TYPE_TKIP
            profile.key = password

        elif is_open(found_profile) or (not found_profile and not password):
            profile.akm = [const.AKM_TYPE_NONE]
            profile.cipher = const.CIPHER_TYPE_NONE
        else:
            if password:
                profile.akm = [const.AKM_TYPE_WPA2PSK]
                profile.cipher = const.CIPHER_TYPE_CCMP
                profile.key = password
            else:
                raise ConnectionAuthenticationError(
                    f"The security mode for '{target}' could not be determined, and no password was provided."
                )

        with self.lock:
            self.iface.disconnect()
        t0 = time.time()
        while time.time() - t0 < 5:
            if self.iface.status() == const.IFACE_DISCONNECTED:
                break
            time.sleep(0.2)

        with self.lock:
            for p in self.iface.network_profiles():
                if p.ssid == target:
                    self.iface.remove_network_profile(p)

        add_ok = True
        try:
            with self.lock:
                tmp_profile = self.iface.add_network_profile(profile)
                if not tmp_profile:
                    add_ok = False
        except Exception:
            add_ok = False 

        if add_ok:
            with self.lock:
                self.iface.connect(tmp_profile)

            t0 = time.time()
            while time.time() - t0 < 30:
                if self.iface.status() == const.IFACE_CONNECTED:
                    ssid_ok = True
                    if sys.platform == "win32":
                        ssid_ok = (self._current_ssid_windows() == target)
                    if ssid_ok:
                        print(f"Successfully connected to {target}.")
                        
                        self._tftp_client = TftpClient(target, 69)
                        return Connection(
                            device=target,
                            hardwarePN="HW-PN-REAL-WIFI",
                            address="192.168.1.1",
                            connectedAt=int(time.time()),
                            pauseHealthCheck=False
                        )
                time.sleep(0.5)

            with self.lock:
                self.iface.disconnect()

        if sys.platform == "win32":
            iface_name = getattr(self.iface, "name", None)
            if not iface_name:
                iface_name = "Wi-Fi"
            wpa2 = True
            if found_profile and const.AKM_TYPE_WPAPSK in found_profile.akm:
                wpa2 = False
            ok = self._win_fallback_connect(iface_name, target, password, wpa2=wpa2)
            if ok:
                print(f"Successfully connected to {target} (via NETSH fallback).")
                        
                self._tftp_client = TftpClient(target, 69)
                return Connection(
                    device=target,
                    hardwarePN="HW-PN-REAL-WIFI",
                    address="192.168.1.1",
                    connectedAt=int(time.time()),
                    pauseHealthCheck=False
                )

        raise ConnectionAuthenticationError(
            f"Failed to connect to '{target}' (invalid profile/timeout)."
        )


    def disconnect(self) -> None:
        print("Disconnecting (pywifi)")
        with self.lock:
            self.iface.disconnect()

    
    # [BST-226]
    def sendPackage(self, pkg: Package) -> None:
        if (self._tftp_client is None):
            raise Exception("Not connected")
        
        self._tftp_client.upload(pkg.name, pkg.path, timeout=60, retries=3)
    
    # [BST-226]
    def receivePackage(self, file_name: str) -> Package:
        if (self._tftp_client is None):
            raise Exception("Not connected")
        
        file_path = f'tmp/client/{int(time.time())}-{file_name}'
        self._tftp_client.download(file_name, file_path, timeout=60, retries=3)

        return Package(file_name, file_path)
    
    def sendRequest(self, req: Request, timeout: int) -> Response: 
        print(f"Sending request (mock): {req.command} with timeout {timeout}")
        if req.command == "GET_HARDWARE_PN":
            return Response(status="SUCCESS", data="HW-PN-MOCK-123") 
        if req.command == "HEALTH_CHECK":
            return Response(status="SUCCESS", data="STATUS_OK") 
        if req.command == "TIMEOUT_REQ":
            time.sleep(timeout + 1)
            raise RequestTimeoutError("Request timed out")
        return Response(status="ERROR", data="DEFAULT_RESPONSE_MOCK") 