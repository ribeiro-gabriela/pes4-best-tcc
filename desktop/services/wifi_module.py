from typing import List
import time
import traceback
from tftpy import TftpClient

import subprocess, tempfile, os

from data.classes import Connection, Package, Request, Response
from data.errors import RequestTimeoutError, ConnectionAuthenticationError

import _wmi

class WifiModule:
    _PASSWORD = "bcappassword"
    _tftp_client: TftpClient | None = None

    def scan(self) -> List[dict]: 
        networks = []
        try:
            subprocess.run(['netsh', 'wlan', 'disconnect'])
            result = str(subprocess.check_output(
                ['netsh', 'wlan', 'show', 'networks', 'mode=bssid'],
                text=True
            ))

            ssids = self._parse_netsh_output(result)

            for profile in ssids:
                ssid = profile["ssid"]
                signal = int(profile["bssids"][0]["signal"][:-1])
                security_type = profile["authentication"]
                
                if not ssid:
                    continue
                
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
            
        networks = [n for n in networks if n.get("info", {}).get("security") == "WPA3-Personal"]
        networks.sort(key=lambda x: int(x['info']['signal'].split(' ')[0]) if 'dBm' in x['info']['signal'] else -100)
        
        return networks

    def _parse_netsh_output(self, result):
        ssids = []
        current_ssid = None
        current_bssid = None
            
        lines = result.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

                # Split key and value
            if ':' in line:
                key_part, value_part = line.split(':', 1)
                key = key_part.strip()
                value = value_part.strip()

                    # Case A: New Network (SSID) detected
                if key.startswith('SSID'):
                        # Save the previous network if it exists
                    if current_ssid:
                        ssids.append(current_ssid)
                        
                        # Initialize new network dict
                    current_ssid = {
                            'ssid': value, 
                            'bssids': []
                        }
                    current_bssid = None # Reset BSSID context
                    
                    # Case B: New BSSID detected
                elif key.startswith('BSSID'):
                    if current_ssid is not None:
                        current_bssid = {'bssid': value}
                        current_ssid['bssids'].append(current_bssid)
                    
                    # Case C: Property (Signal, Radio type, Authentication, etc.)
                else:
                        # Logic: If we are inside a BSSID context, add property there.
                        # Otherwise, add it to the main Network context.
                    clean_key = key.lower().replace(' ', '_')
                        
                    if current_bssid is not None:
                        current_bssid[clean_key] = value
                    elif current_ssid is not None:
                        current_ssid[clean_key] = value

            # Append the final network after the loop finishes
        if current_ssid:
            ssids.append(current_ssid)
        return ssids

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

    def _win_fallback_connect(self, ssid: str, password: str):
        xml = f'''<?xml version="1.0"?>
    <WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>{ssid}</name>
    <SSIDConfig><SSID><name>{ssid}</name></SSID></SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>manual</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA3SAE</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>{password}</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>
'''

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".xml", encoding="utf-8") as f:
            f.write(xml)
            xml_path = f.name

        try:
            subprocess.check_call(["netsh", "wlan", "add", "profile", f'filename="{xml_path}"'])
            subprocess.check_call(f'netsh wlan connect name="{ssid}" ssid="{ssid}"', shell=True)
        except Exception as e:
            print(e)
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

    def _get_target_ip(self) -> str:
        # Retrieves subnet using wmic, filtering for IPEnabled adapters
        cmd = 'wmic nicconfig where IPEnabled=True get DefaultIPGateway /format:csv'
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        for line in result.stdout.splitlines():
            if ',' in line and '{' in line: # Look for data lines with curly braces
                # wmic returns subnets as {"255.255.255.0", "64"} (IPv4, IPv6)
                # We strip the braces and take the first one
                parts = line.split(',')
                if len(parts) > 1:
                    raw_subnet = parts[1].strip('{}').replace('"', '')
                    return raw_subnet.split(';')[0] # Return just the first IPv4 mask
        raise ConnectionError("Cannot get target IP")

    def connect(self, target: str, password: str|None = None) -> Connection:
        print(f"Attempting to connect to {target}" + (f" with password: {'*' * len(password)}" if password else " (no password)"))
        
        if not password:
            password = self._PASSWORD
        
        # with self.lock:
        #     self.iface.scan()
        # time.sleep(2)
        # with self.lock:
        #     scan_results = self.iface.scan_results()

        # found_profile = next((p for p in scan_results if p.ssid == target), None)

        # profile = found_profile

        # if not found_profile:
        #     profile = pywifi.Profile()
        #     profile.ssid = target
        #     profile.auth = const.AUTH_ALG_OPEN
        #     profile.akm = []
        #     profile.cipher = const.CIPHER_TYPE_NONE

        #     def is_psk(p):
        #         return p and (const.AKM_TYPE_WPA2PSK in p.akm or const.AKM_TYPE_WPAPSK in p.akm)
        #     def is_open(p):
        #         return p and (const.AKM_TYPE_NONE in p.akm)

        #     if is_psk(found_profile):
        #         if not password:
        #             raise ConnectionAuthenticationError(f"Network '{target}' requires a password (WPA/WPA2-PSK).")
        #         if const.AKM_TYPE_WPA2PSK in found_profile.akm:
        #             profile.akm = [const.AKM_TYPE_WPA2PSK]
        #             profile.cipher = const.CIPHER_TYPE_CCMP
        #         elif const.AKM_TYPE_WPAPSK in found_profile.akm:
        #             profile.akm = [const.AKM_TYPE_WPAPSK]
        #             profile.cipher = const.CIPHER_TYPE_TKIP
        #         profile.key = password

        #     elif is_open(found_profile) or (not found_profile and not password):
        #         profile.akm = [const.AKM_TYPE_NONE]
        #         profile.cipher = const.CIPHER_TYPE_NONE
        #     else:
        #         if password:
        #             profile.akm = [const.AKM_TYPE_WPA2PSK]
        #             profile.cipher = const.CIPHER_TYPE_CCMP
        #             profile.key = password
        #         else:
        #             raise ConnectionAuthenticationError(
        #                 f"The security mode for '{target}' could not be determined, and no password was provided."
        #             )

        # profile.key = password

        # with self.lock:
        #     self.iface.disconnect()
        # t0 = time.time()
        # while time.time() - t0 < 5:
        #     if self.iface.status() == const.IFACE_DISCONNECTED:
        #         break
        #     time.sleep(0.2)

        # with self.lock:
        #     for p in self.iface.network_profiles():
        #         if p.ssid == target:
        #             self.iface.remove_network_profile(p)

        # add_ok = True
        # try:
        #     with self.lock:
        #         tmp_profile = self.iface.add_network_profile(profile)
        #         if not tmp_profile:
        #             add_ok = False
        # except Exception:
        #     add_ok = False 

        # if add_ok:
        #     with self.lock:
        #         self.iface.connect(tmp_profile)

        #     t0 = time.time()
        #     while time.time() - t0 < 30:
        #         if self.iface.status() == const.IFACE_CONNECTED:
        #             ssid_ok = True
        #             if sys.platform == "win32":
        #                 ssid_ok = (self._current_ssid_windows() == target)
        #             if ssid_ok:
        #                 print(f"Successfully connected to {target}.")
                        
        #                 self._tftp_client = TftpClient(target, 69)
        #                 return Connection(
        #                     device=target,
        #                     hardwarePN="HW-PN-REAL-WIFI",
        #                     address="192.168.1.1",
        #                     connectedAt=int(time.time()),
        #                     pauseHealthCheck=False
        #                 )
        #         time.sleep(0.5)

        #     with self.lock:
        #         self.iface.disconnect()

        # if sys.platform == "win32":
        # iface_name = self.iface.name()
        # if not iface_name:
        #     iface_name = "Wi-Fi"
        # wpa2 = True
        # if found_profile and const.AKM_TYPE_WPAPSK in found_profile.akm:
        #     wpa2 = False
        ok = self._win_fallback_connect(target, password)
        if ok:
            print(f"Successfully connected to {target} (via NETSH fallback).")
            ip = self._get_target_ip()
            self._tftp_client = TftpClient(ip, 69)
            return Connection(
                device=target,
                hardwarePN="",
                address=ip,
                connectedAt=int(time.time()),
                pauseHealthCheck=False
            )

        raise ConnectionAuthenticationError(
            f"Failed to connect to '{target}' (invalid profile/timeout)."
        )


    def disconnect(self) -> None:
        subprocess.run(['netsh', 'wlan', 'disconnect'])
    
    # [BST-226]
    def sendPackage(self, pkg: Package) -> None:
        if (self._tftp_client is None):
            raise Exception("Not connected")
        
        self._tftp_client.upload(pkg.name, pkg.path, timeout=60, retries=3)
    
    # [BST-226]
    def receivePackage(self, file_name: str) -> Package:
        if (self._tftp_client is None):
            raise Exception("Not connected")
        
        file_path = f'tftp/client/{int(time.time())}-{file_name}'
        self._tftp_client.download(file_name, file_path, timeout=60, retries=3)

        return Package(file_name, file_path)
    
    def sendRequest(self, req: Request, timeout: int) -> Response: 
        print(f"Sending request (mock): {req.command} with timeout {timeout}")
        if req.command == "GET_HARDWARE_PN":
            return Response(status="SUCCESS", data="EMB-HW-002-021-003") 
        if req.command == "HEALTH_CHECK":
            return Response(status="SUCCESS", data="STATUS_OK") 
        if req.command == "TIMEOUT_REQ":
            time.sleep(timeout + 1)
            raise RequestTimeoutError("Request timed out")
        return Response(status="ERROR", data="DEFAULT_RESPONSE_MOCK") 