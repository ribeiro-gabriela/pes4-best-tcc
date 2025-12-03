import time
import threading
from typing import Optional, List

from data.classes import Connection, Package, Request, Response
from data.errors import ConnectionAuthenticationError, DisconnectedError, RequestTimeoutError
from interfaces.connection_transport import IConnectionTransport
from services.logging_service import LoggingService

from ui.event_router import emit_event
from data.events import Event

class ConnectionService:
    def __init__(self, wifi_module: IConnectionTransport, test_mode: bool = True):
        self.logging_service = LoggingService(ConnectionService.__name__)
        self.wifi_module = wifi_module
        self.test_mode = test_mode  # Flag para modo de teste com hardware PN simulado
        
        # [BST-225]
        # [BST-219]
        # [BST-214]
        # [BST-207]
        self.currentConnection: Optional[Connection] = None
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()
        self._retry_lock = threading.Lock()

    def _perform_authentication(self, conn: Connection) -> bool:
        # [BST-220]
        return True

    def _handle_reconnection(self):
        if not self.currentConnection:
            raise DisconnectedError("Not Connected")
        
        if not self._retry_lock.acquire(blocking=False):
            return

        try:
            # [BST-212]
            self.logging_service.log("Starting connection retry policy...")
            
            if self.currentConnection:
                # [BST-213]
                self.wifi_module.disconnect()

            device = self.currentConnection.device    
            # [BST-207]
            self.currentConnection = None
            
            # [BST-206]
            emit_event(Event(Event.EventType.RECONNECTION))
            
            retry_attempts = 3
            success = False

            for i in range(retry_attempts):
                try:
                    self.connect(device) 
                    if self.isConnected():
                        success = True
                        break
                except Exception as e:
                    self.logging_service.error(f"Retry attempt {i+1} failed", e)
                    time.sleep(5) 

            if success:
                # [BST-205]
                emit_event(Event(Event.EventType.RECONNECTION_SUCCESS))
                self.logging_service.log("Reconnection successful.")
            else:
                # [BST-207]
                self.currentConnection = None
                emit_event(Event(Event.EventType.DISCONNECT))
                raise ConnectionError("Reconnection failed.")
        finally:
            self._retry_lock.release()

    def _health_check_loop(self):
        # [BST-210]
        while not self._stop_health_check.is_set():
            # [BST-210]
            if self.currentConnection and not self.currentConnection.pauseHealthCheck:
                try:
                    # [BST-210]
                    self.sendRequest(Request(command="HEALTH_CHECK"))
                except (RequestTimeoutError, ConnectionError) as e:
                    # [BST-212]
                    self.logging_service.error("Health check failed, initiating retry...", e)
                    self._handle_reconnection()
                    break 
            
            # [BST-210]
            self._stop_health_check.wait(60)

    def _start_health_check(self):
        # [BST-210]
        if not self._health_check_thread or not self._health_check_thread.is_alive():
            self._stop_health_check.clear()
            self._health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
            self._health_check_thread.start()

    def scan(self) -> List[dict]:
        # [BST-222]
        networks = self.wifi_module.scan() 
        # [BST-223]
        consolidated_networks = {}
        for network in networks:
            ssid = network["ssid"]
            signal = network["info"]["signal"]
            if ssid not in consolidated_networks or signal > consolidated_networks[ssid]["info"]["signal"]:
                consolidated_networks[ssid] = network
        return list(consolidated_networks.values())

    def connect(self, target: str, password: str|None = None):
        # [BST-224]
        self.logging_service.log("Attempting connection...")
        try:
            # [BST-218] 
            connection_base = self.wifi_module.connect(target, password)
            
            # [BST-220]
            auth_success = self._perform_authentication(connection_base)
            
            if not auth_success:
                # [BST-221]
                raise ConnectionAuthenticationError("BC Module Authentication Failed")

            # [BST-219]
            self.currentConnection = connection_base
            
            # [BST-215] 
            if self.test_mode:
                # Modo de teste: usa hardware PN simulado
                hardware_pn = f"HW-PN-TEST-{target.upper().replace(' ', '-')}"
                self.logging_service.log(f"Test mode: Using simulated hardware PN: {hardware_pn}")
            else:
                # Modo real: tenta obter hardware PN do dispositivo
                try:
                    # hardware_pn_response = self.sendRequest(Request(command="GET_HARDWARE_PN"))
                    # hardware_pn = hardware_pn_response.data
                    hardware_pn = "EMB-" + self.currentConnection.device.split("EMB-", 1)[1]
                except Exception as hw_error:
                    hardware_pn = f"HW-PN-FALLBACK-{target.upper().replace(' ', '-')}"
                    self.logging_service.log(f"Hardware PN request failed, using fallback: {hardware_pn}. Error: {hw_error}")
            
            # [BST-216]
            self.currentConnection.hardwarePN = hardware_pn
            
            # [BST-224]
            self.logging_service.log(f"Connection successful. HW_PN: {hardware_pn}")

            emit_event(Event(Event.EventType.CONNECTION_SUCCESS, properties={"target": hardware_pn}))
            
            # [BST-210]
            self._start_health_check()

        except ConnectionAuthenticationError as e: 
            self.logging_service.error(f"Authentication failed for {target}", e)
            emit_event(Event(Event.EventType.CONNECTION_FAILURE, properties={"message": f"Authentication failed for '{target}': {e}"}))
            self.currentConnection = None 

        except Exception as e:
            # [BST-224]
            self.logging_service.error("Connection failed", e)
            emit_event(Event(Event.EventType.ERROR, error=e, properties={"message": f"Failed to connect to {target}: {e}"}))
            self.currentConnection = None
            if isinstance(e, (ConnectionError, RequestTimeoutError)):
                pass
            else:
                raise e

    def disconnect(self):
        # [BST-224]
        self.logging_service.log("Attempting disconnection...")
        if self.currentConnection:
            try:
                # [BST-210]
                if self._health_check_thread:
                    self._stop_health_check.set()
                    self._health_check_thread.join()
                    
                # [BST-213]
                self.wifi_module.disconnect()
                # [BST-224]
                self.logging_service.log("Disconnection successful.")
            except Exception as e:
                # [BST-224]
                self.logging_service.error("Disconnection failed", e)
                raise e
            finally:
                # [BST-213]
                # [BST-214]
                self.currentConnection = None
        else:
            # [BST-224]
            self.logging_service.log("Disconnection attempt: No active connection.")

    def isConnected(self) -> bool:
        # [BST-225]
        return self.currentConnection is not None

    def getConnectionHardwarePN(self) -> str:
        if self.currentConnection:
            # [BST-217]
            return self.currentConnection.hardwarePN
        raise DisconnectedError("Not connected")

    # [BST-226]
    def sendPackage(self, package: Package):
        # [BST-224]
        self.logging_service.log("Sending package...")
        if not self.isConnected():
            err = ConnectionError("Cannot send package: Not connected.")
            self.logging_service.error("SendPackage failed", err)
            raise err
        
        try:
            self.wifi_module.sendPackage(package)
            # [BST-224]
            self.logging_service.log("SendPackage successful.")
        except Exception as e:
            # [BST-224]
            self.logging_service.error("SendPackage failed", e)
            # [BST-212]
            self._handle_reconnection()
            raise ConnectionError("SendPackage failed, connection lost.") from e

    # [BST-226]
    def receivePackage(self, file_name: str) -> Package:
        # [BST-224]
        self.logging_service.log("Receiving package...")
        if not self.isConnected():
            err = ConnectionError("Cannot receive package: Not connected.")
            self.logging_service.error("ReceivePackage failed", err)
            raise err

        try:
            data = self.wifi_module.receivePackage(file_name)
            # [BST-224]
            self.logging_service.log("ReceivePackage successful.")
            return data
        except Exception as e:
            # [BST-224]
            self.logging_service.error("ReceivePackage failed", e)
            # [BST-212]
            self._handle_reconnection()
            raise ConnectionError("ReceivePackage failed, connection lost.") from e
    
    def sendRequest(self, request: Request) -> Response:
        # [BST-224]
        self.logging_service.log(f"Sending request: {request.command}")
        if not self.isConnected():
            err = ConnectionError(f"Cannot send request '{request.command}': Not connected.")
            self.logging_service.error("SendRequest failed", err)
            raise err
            
        try:
            # [BST-211]
            timeout = 60
            response = self.wifi_module.sendRequest(request, timeout=timeout)
            # [BST-224]
            self.logging_service.log(f"SendRequest successful. Response: {response.status}")
            return response
        
        except RequestTimeoutError as e:
            # [BST-211]
            # [BST-224]
            self.logging_service.error(f"SendRequest '{request.command}' timed out", e)
            # [BST-212]
            self._handle_reconnection()
            raise e
            
        except Exception as e:
            # [BST-224]
            self.logging_service.error(f"SendRequest '{request.command}' failed", e)
            # [BST-212]
            self._handle_reconnection()
            raise ConnectionError(f"SendRequest '{request.command}' failed.") from e

    def pauseHealthCheck(self):
        if self.currentConnection:
            # [BST-208]
            self.currentConnection.pauseHealthCheck = True
            self.logging_service.log("Health check paused.")

    def resumeHealthCheck(self):
        if self.currentConnection:
            # [BST-209]
            self.currentConnection.pauseHealthCheck = False
            self.logging_service.log("Health check resumed.")