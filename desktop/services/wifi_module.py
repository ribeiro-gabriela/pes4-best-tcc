from typing import Any, List
import pywifi
from pywifi import const
import time

from data.classes import Connection, Package, Request, Response
from data.errors import RequestTimeoutError

from tftpy import TftpClient, TftpServer

from services.logging_service import LoggingService


class WifiModule:
    _target_host: str | None = None
    _tftp_client: TftpClient | None = None

    def __init__(self):
        self.logging_service = LoggingService(WifiModule.__name__)

    # [BST-222]
    def scan(self) -> List[str]:
        # [BST-223]
        connections = self.get_wifi_connections()
        return [conn['ssid'] for conn in connections]

    # [BST-218]
    def connect(self, target: str) -> Connection:
        self._target_host = "192.168.1.1"
        self._tftp_client = TftpClient(target, 69)

        return Connection(
            device="MockBC", 
            hardwarePN="", 
            address="192.168.1.1", 
            connectedAt=int(time.time()),
            pauseHealthCheck=False
        )

    # [BST-213]
    def disconnect(self) -> None:
        self._target_host = None
        self._tftp_client = None
        pass

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
    
    # [BST-211]
    def sendRequest(self, req: Request, timeout: int) -> Response|Any:
        if req == "GET_HARDWARE_PN":
            # [BST-215]
            return "HW-PN-MOCK-123"
        if req == "HEALTH_CHECK":
            # [BST-210]
            return "STATUS_OK"
        if req == "TIMEOUT_REQ":
            time.sleep(timeout + 1)
            raise RequestTimeoutError("Request timed out")
        return "DEFAULT_RESPONSE"
    

    """
    Scans for and returns a list of available WiFi networks.
    Each dictionary contains the SSID, signal strength, and security type.
    """
    # [BST-222]
    def get_wifi_connections(self) -> list[dict]:
        networks = []
        try:
            wifi = pywifi.PyWiFi()
            iface = wifi.interfaces()[0]  # Get the first available wifi interface

            iface.scan()
            time.sleep(0.1)  # Wait for the scan to complete
            scan_results = iface.scan_results()

            for profile in scan_results:
                ssid = profile.ssid
                signal = profile.signal
                security_type = "Unknown"
                
                if not ssid:
                    continue

                # Determine security type from AKM (Authentication and Key Management)
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
                
                # Avoid duplicate SSIDs, keeping the one with the strongest signal
                existing_network = next((net for net in networks if net['ssid'] == ssid), None)
                if existing_network:
                    self.logging_service.log(existing_network)
                    if signal > int(existing_network['info']['signal'].replace(' dBm', '')):
                        existing_network['info']['signal'] = f"{signal} dBm"
                else:
                    networks.append({"ssid": ssid, "info":{"signal": f"{signal} dBm", "security": security_type}})
                    
        except Exception as e:
            raise Exception("Error scanning for WiFi networks", e)
            
        # Sort by signal strength (strongest first)
        networks.sort(key=lambda x: int(x['info']['signal'].split(' ')[0]) if 'dBm' in x['info']['signal'] else -100, reverse=True)
        
        return networks