import re
from typing import List
import time
import traceback
from tftpy import TftpClient

import subprocess, tempfile, os

from data.classes import Connection, Package, Request, Response
from data.errors import RequestTimeoutError, ConnectionAuthenticationError
from interfaces.connection_transport import IConnectionTransport

class WifiModule(IConnectionTransport):
    _PASSWORD = "bcappassword"
    _tftp_client: TftpClient | None = None

    def scan(self) -> List[dict]: 
        networks = []
        try:
            subprocess.run(['netsh', 'wlan', 'disconnect'])
            time.sleep(0.1)
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
            
        networks = [n for n in networks if n.get("info", {}).get("security") == "WPA3-Personal" and "EMB-" in n.get("ssid", "")]
        networks.sort(key=lambda x: int(x['info']['signal'].split(' ')[0]) if 'dBm' in x['info']['signal'] else -100)
        
        return networks

    def _parse_netsh_output(self, result):
        # 1. Define the standard order of properties for Windows Netsh
        # CAUTION: If Windows updates the netsh output format, this order might shift.
        SSID_PROPERTIES = [
            'network_type',
            'authentication',
            'encryption'
        ]
        
        BSSID_PROPERTIES = [
            'signal',
            'radio_type',
            'channel',
            'basic_rates',
            'other_rates'
        ]

        networks = []
        current_network = None
        current_bssid = None
        
        # Counters to track which position we are at within a block
        ssid_prop_index = 0
        bssid_prop_index = 0

        # Regex to catch "SSID 1 :" or "BSSID 1 :"
        # These terms are technical acronyms and usually persistent across languages
        header_pattern = re.compile(r'^\s*(SSID|BSSID)\s+(\d+)\s*:\s*(.*)$')

        lines = result.splitlines()

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for Headers (SSID/BSSID)
            header_match = header_pattern.match(line)
            
            if header_match:
                header_type = header_match.group(1) # SSID or BSSID
                value = header_match.group(3).strip()

                if header_type == 'SSID':
                    # Save previous network
                    if current_network:
                        networks.append(current_network)
                    
                    # Start new Network
                    current_network = {
                        'ssid': value if value else 'Hidden Network',
                        'bssids': []
                    }
                    current_bssid = None
                    ssid_prop_index = 0 # Reset counter for new SSID block

                elif header_type == 'BSSID':
                    # Start new BSSID
                    if current_network is not None:
                        current_bssid = {'bssid': value}
                        current_network['bssids'].append(current_bssid)
                        bssid_prop_index = 0 # Reset counter for new BSSID block

                continue

            # Process Properties (Lines with :)
            if ':' in line:
                # We ignore the key (left side) entirely to avoid language issues
                _, value = line.split(':', 1)
                value = value.strip()

                # Decide where to map this value based on context
                if current_bssid is not None:
                    # We are inside a BSSID block
                    if bssid_prop_index < len(BSSID_PROPERTIES):
                        key_name = BSSID_PROPERTIES[bssid_prop_index]
                        current_bssid[key_name] = value
                        bssid_prop_index += 1
                    else:
                        # Capture overflow properties just in case
                        current_bssid[f'extra_prop_{bssid_prop_index}'] = value
                        bssid_prop_index += 1

                elif current_network is not None:
                    # We are inside an SSID block (but not yet in a BSSID)
                    if ssid_prop_index < len(SSID_PROPERTIES):
                        key_name = SSID_PROPERTIES[ssid_prop_index]
                        current_network[key_name] = value
                        ssid_prop_index += 1

        # Append the final network
        if current_network:
            networks.append(current_network)

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

    def _win_fallback_connect(self, ssid: str, password: str):
        cur = self._current_ssid_windows()
        if cur == ssid:
            return True

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
        cmd = ["powershell", "-Command", "(Get-WmiObject -Class Win32_NetworkAdapterConfiguration -Filter 'IPEnabled=True').DefaultIPGateway"]
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        
        for line in result.stdout.splitlines():
            if '192' in line:
                return line.strip()
        raise ConnectionError("Cannot get target IP")

    def connect(self, target: str, password: str|None = None) -> Connection:
        print(f"Attempting to connect to {target}" + (f" with password: {'*' * len(password)}" if password else " (no password)"))
        
        if not password:
            password = self._PASSWORD
        
        ok = self._win_fallback_connect(target, password)
        if ok:
            print(f"Successfully connected to {target} (via NETSH fallback).")
            time.sleep(0.2)
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
        
        file_path = f'file_directory/tftp/client/{int(time.time())}-{file_name}'
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
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