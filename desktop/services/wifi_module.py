from typing import List
import time
import traceback
from tftpy import TftpClient

import subprocess, os, re

from data.classes import Connection, Package, Request, Response
from data.errors import RequestTimeoutError, ConnectionAuthenticationError

class WifiModule:
    _PASSWORD = "bcappassword"
    _tftp_client: TftpClient | None = None
    # _interface: str | None = None

    # def __init__(self):
    #     # Auto-detect the wireless interface name (e.g., wlan0, wlp3s0)
    #     self._interface = self._get_wifi_interface()

    def _get_wifi_interface(self) -> str:
        """Helper to find the wireless interface name on Linux."""
        try:
            # listing devices, filtering for wifi, getting the device name column
            result = subprocess.check_output(
                ['nmcli', '-t', '-f', 'DEVICE,TYPE', 'device'], text=True
            )
            for line in result.splitlines():
                if ":wifi" in line:
                    return line.split(":")[0]
        except Exception:
            pass
        return "wlan0" # Fallback default

    def scan(self) -> List[dict]:
        networks = []
        try:
            # Force a fresh scan
            subprocess.run(['nmcli', 'device', 'wifi', 'rescan'], capture_output=True)
            time.sleep(1) # Give it a moment to populate

            # nmcli -t (terse) -f (fields)
            # SSID, SIGNAL (0-100), SECURITY, BSSID
            cmd = ['nmcli', '-t', '-f', 'SSID,SIGNAL,SECURITY,BSSID', 'device', 'wifi', 'list']
            result = subprocess.check_output(cmd, text=True)

            parsed_ssids = self._parse_nmcli_output(result)

            for profile in parsed_ssids:
                ssid = profile["ssid"]
                signal = int(profile["signal"])
                security_type = profile["security"]
                
                if not ssid:
                    continue
                
                # Logic to keep the strongest signal if SSID appears multiple times
                existing_network = next((net for net in networks if net['ssid'] == ssid), None)
                
                if existing_network:
                    # Parse existing signal (format "XX dBm" from previous loop)
                    existing_signal_str = existing_network['info']['signal'].split(' ')[0]
                    existing_signal_int = int(existing_signal_str) if existing_signal_str.replace('-','').isdigit() else -100
                    
                    if signal > existing_signal_int:
                        existing_network['info']['signal'] = f"{signal} dBm"
                else:
                    # Note: nmcli gives signal in bars (0-100), netsh gave it in %. 
                    # We append ' dBm' to maintain compatibility with your UI/Logic, 
                    # even though strictly speaking this is a percentage/quality score, not raw dBm.
                    networks.append({"ssid": ssid, "info": {"signal": f"{signal} dBm", "security": security_type}})
                      
        except Exception as e:
            print(f"Error scanning for WiFi networks: {traceback.format_exc()}")
            return [{"ssid": "Scan Error", "info": {"signal": "N/A", "security": str(e)}}]
            
        # Filter for WPA3 if required, or general WPA. 
        # Note: nmcli returns strings like "WPA2 WPA3". 
        networks = [n for n in networks if "WPA3" in n.get("info", {}).get("security", "").upper()]
        
        # Sort by signal strength descending
        networks.sort(key=lambda x: int(x['info']['signal'].split(' ')[0]), reverse=True)
        
        return networks

    def _parse_nmcli_output(self, result: str) -> List[dict]:
        """
        Parses: SSID:SIGNAL:SECURITY:BSSID
        Note: Escaped colons in SSIDs are handled by nmcli terse mode usually, 
        but simple split is safer for standard SSIDs.
        """
        parsed = []
        for line in result.splitlines():
            if not line: continue
            
            # nmcli terse uses ':' as separator. 
            # To be safe against SSIDs containing colons, we split carefully or assume standard naming.
            # A robust regex for nmcli terse output:
            parts = line.split(':')
            if len(parts) < 3: continue

            # Handle cases where SSID might have colons (rare but possible)
            # We know the last 3 items are always BSSID (mac), SECURITY, SIGNAL.
            # Actually nmcli order requested was: SSID,SIGNAL,SECURITY,BSSID
            
            bssid = parts[-1]
            security = parts[-2]
            signal = parts[-3]
            ssid = ":".join(parts[:-3]) # Join back the rest as SSID

            # Start normalizing
            # NMCLI security often looks like "WPA2 802.1X" or "WPA3 SAE"
            
            parsed.append({
                "ssid": ssid.replace('\\:', ':'), # unescape if nmcli escaped it
                "signal": signal,
                "security": security,
                "bssid": bssid
            })
        return parsed

    def _get_current_ssid_linux(self) -> str | None:
        try:
            # nmcli -t -f ACTIVE,SSID device wifi
            # Returns lines like: "yes:MyHomeWifi" or "no:OtherWifi"
            out = subprocess.check_output(
                ["nmcli", "-t", "-f", "ACTIVE,SSID", "device", "wifi"],
                text=True, errors="ignore"
            )
            for line in out.splitlines():
                if line.startswith("yes:"):
                    return line.split(":", 1)[1]
        except Exception:
            pass
        return None

    def _linux_connect(self, ssid: str, password: str) -> bool:
        """
        Connects using NetworkManager.
        """
        # print(f"Connecting to {ssid} on interface {self._interface}...")
        try:
            # Disconnect current connection first to be clean
            # subprocess.run(['nmcli', 'device', 'disconnect', self._interface], capture_output=True)
            
            # Connect command
            cmd = ['nmcli', 'device', 'wifi', 'connect', ssid, 'password', password]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"nmcli connection failed: {result.stderr}")
                return False

            # Verify connection
            t0 = time.time()
            while time.time() - t0 < 15:
                cur = self._get_current_ssid_linux()
                if cur == ssid:
                    return True
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Connection exception: {e}")
            
        return False

    def _get_target_ip(self) -> str:
        """
        Retrieves the default gateway IP using 'ip route'.
        This assumes the target device acts as the gateway.
        """
        try:
            # Command: ip route show default
            # Output example: "default via 192.168.1.1 dev wlan0 proto dhcp src 192.168.1.105 metric 600"
            result = subprocess.check_output(['ip', 'route', 'show', 'default'], text=True)
            
            match = re.search(r'default via ([\d\.]+)', result)
            if match:
                return match.group(1)
                
        except Exception as e:
            print(f"Error getting gateway IP: {e}")

        raise ConnectionError("Cannot get target IP (Gateway)")

    def connect(self, target: str, password: str|None = None) -> Connection:
        print(f"Attempting to connect to {target}" + (f" with password: {'*' * len(password)}" if password else " (no password)"))
        
        if not password:
            password = self._PASSWORD
        
        ok = self._linux_connect(target, password)
        
        if ok:
            print(f"Successfully connected to {target} (via NMCLI).")
            try:
                ip = self._get_target_ip()
                self._tftp_client = TftpClient(ip, 69)
                return Connection(
                    device=target,
                    hardwarePN="",
                    address=ip,
                    connectedAt=int(time.time()),
                    pauseHealthCheck=False
                )
            except Exception as e:
                 # If we connected to wifi but can't get IP, we must disconnect
                self.disconnect()
                raise e

        raise ConnectionAuthenticationError(
            f"Failed to connect to '{target}' (invalid password or timeout)."
        )

    def disconnect(self) -> None:
        subprocess.run(['nmcli', 'device', 'disconnect'])
        # if self._interface:
        #     subprocess.run(['nmcli', 'device', 'disconnect', self._interface])
    
    # [BST-226] - Unchanged logic
    def sendPackage(self, pkg: Package) -> None:
        if (self._tftp_client is None):
            raise Exception("Not connected")
        
        self._tftp_client.upload(pkg.name, pkg.path, timeout=60, retries=3)
    
    # [BST-226] - Unchanged logic
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