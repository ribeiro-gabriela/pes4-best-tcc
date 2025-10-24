from typing import Any, List
import pywifi
from pywifi import const
import time

import traceback

from data.classes import Connection, Package, Request, Response
from data.errors import RequestTimeoutError

"""
Scans for and returns a list of available WiFi networks.
Each dictionary contains the SSID, signal strength, and security type.
"""
def get_wifi_connections() -> list[dict]:

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
                print(existing_network)
                if signal > int(existing_network['info']['signal'].replace(' dBm', '')):
                    existing_network['info']['signal'] = f"{signal} dBm"
            else:
                 networks.append({"ssid": ssid, "info":{"signal": f"{signal} dBm", "security": security_type}})
                 
    except Exception as e:
        print(f"Error scanning for WiFi networks: {traceback.format_exc()}")
        return [{"ssid": "Scan Error", "info":{"signal": "N/A", "security": str(e)}}]
        
    # Sort by signal strength (strongest first)
    networks.sort(key=lambda x: int(x['info']['signal'].split(' ')[0]) if 'dBm' in x['info']['signal'] else -100, reverse=True)
    
    return networks


class WifiModule:
    # [BST-222]
    def scan(self) -> List[str]:
        # [BST-223]
        return ["WIFI_MOCK_1", "WIFI_MOCK_2"]

    # [BST-218]
    def connect(self, target: str) -> Connection:
        return Connection(
            device="MockBC", 
            hardwarePN="", 
            address="192.168.1.1", 
            connectedAt=str(time.time()),
            pauseHealthCheck=False
        )

    # [BST-213]
    def disconnect(self) -> None:
        pass

    # [BST-226]
    def sendPackage(self, pkg: Package) -> None:
        pass
    
    # [BST-226]
    def receivePackage(self) -> Package:
        return Package()
    
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