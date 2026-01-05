from enum import Enum
import logging

from application.messages import (
    AppMessage, MessageType,
    create_hello_message, create_mode_select_message,
    create_msg_message, create_ack_message,
    create_error_message, create_bye_message
)
from application.encryption import AESEncryption, SimpleXOR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    IDLE = "IDLE"
    HELLO_SENT = "HELLO_SENT"
    CONNECTED = "CONNECTED"
    MODE_NEGOTIATING = "MODE_NEGOTIATING"
    READY = "READY"
    CLOSED = "CLOSED"


class Mode(Enum):
    DEFAULT = "default"              #no encryption, no obfuscation
    SECURE = "secure"                #encryption, no obfuscation
    OBFS = "obfs"                    #no encryption, HTTPS obfuscation
    SECURE_OBFS = "secure_obfs"      #encryption + HTTPS obfuscation


class ApplicationProtocol:
    
    def __init__(self, client_id: str = "client"):
        self.client_id = client_id
        self.state = ConnectionState.IDLE
        self.mode = Mode.DEFAULT
        self.encryption = None
        self.xor = None  # Optional XOR layer
        
    def set_mode(self, mode: Mode):
        self.mode = mode
        logger.info(f"[APP] Mode set to: {mode.value}")
        
        if mode in [Mode.SECURE, Mode.SECURE_OBFS]:
            self.encryption = AESEncryption()
            logger.info(f"[APP] Encryption key: {self.encryption.get_key_b64()}")
        else:
            self.encryption = None
    
    def set_encryption_key(self, key_b64: str):
        self.encryption = AESEncryption.from_key_b64(key_b64)
        logger.info(f"[APP] Encryption key loaded")
    
    def enable_xor(self, key: bytes = b"xorkey"):
        self.xor = SimpleXOR(key)
        logger.info(f"[APP] XOR layer enabled")
    
    def prepare_message(self, app_msg: AppMessage) -> bytes:
        #serialize
        data = app_msg.to_bytes()
        
        #if in secure mode encrypt
        if self.encryption and self.mode in [Mode.SECURE, Mode.SECURE_OBFS]:
            logger.debug(f"[APP] Encrypting message ({len(data)} bytes)")
            data = self.encryption.encrypt(data)
        
        #xor apply
        if self.xor:
            logger.debug(f"[APP] XOR obfuscation")
            data = self.xor.encrypt(data)
        
        return data
    
    def parse_message(self, data: bytes) -> AppMessage:
        #remove XOR if applied
        if self.xor:
            logger.debug(f"[APP] XOR de-obfuscation")
            data = self.xor.decrypt(data)
        
        #decrypt if in secure mode
        if self.encryption and self.mode in [Mode.SECURE, Mode.SECURE_OBFS]:
            logger.debug(f"[APP] Decrypting message ({len(data)} bytes)")
            data = self.encryption.decrypt(data)
        
        # Deserialize
        return AppMessage.from_bytes(data)
    
    #STATE MACHINE METHODS
    
    def send_hello(self) -> AppMessage:
        if self.state != ConnectionState.IDLE:
            raise RuntimeError(f"Cannot send HELLO in state {self.state}")
        
        self.state = ConnectionState.HELLO_SENT
        msg = create_hello_message(self.client_id)
        logger.info(f"[APP] Sent HELLO")
        return msg
    
    def handle_hello(self, msg: AppMessage) -> AppMessage:
        if msg.msg_type != MessageType.HELLO:
            return create_error_message("INVALID_MSG", "Expected HELLO")
        
        client_id = msg.payload.get('client_id', 'unknown')
        logger.info(f"[APP] Received HELLO from {client_id}")
        
        self.state = ConnectionState.CONNECTED
        return create_ack_message()
    
    def send_mode_select(self, mode: Mode) -> AppMessage:
        self.set_mode(mode)
        self.state = ConnectionState.MODE_NEGOTIATING
        
        msg = create_mode_select_message(mode.value)
        logger.info(f"[APP] Sent MODE_SELECT: {mode.value}")
        return msg
    
    def handle_mode_select(self, msg: AppMessage) -> AppMessage:
        if msg.msg_type != MessageType.MODE_SELECT:
            return create_error_message("INVALID_MSG", "Expected MODE_SELECT")
        
        mode_str = msg.payload.get('mode')
        try:
            mode = Mode(mode_str)
            self.set_mode(mode)
            self.state = ConnectionState.READY
            logger.info(f"[APP] Mode negotiated: {mode.value}")
            return create_ack_message()
        except ValueError:
            return create_error_message("INVALID_MODE", f"Unknown mode: {mode_str}")
    
    def send_message(self, text: str) -> AppMessage:
        if self.state != ConnectionState.READY:
            raise RuntimeError(f"Cannot send message in state {self.state}")
        
        msg = create_msg_message(text, sender=self.client_id)
        logger.info(f"[APP] Sent MSG: {text[:30]}...")
        return msg
    
    def handle_message(self, msg: AppMessage) -> str:
        if msg.msg_type != MessageType.MSG:
            raise ValueError("Not a MSG message")
        
        text = msg.payload.get('text', '')
        sender = msg.payload.get('sender', 'unknown')
        logger.info(f"[APP] Received MSG from {sender}: {text[:30]}...")
        return text
    
    def send_bye(self, reason: str = None) -> AppMessage:
        self.state = ConnectionState.CLOSED
        msg = create_bye_message(reason)
        logger.info(f"[APP] Sent BYE")
        return msg


#test code
if __name__ == "__main__":
    print("### Application Protocol Test ###\n")
    
    #test 1: basic flow without encryption
    print("Test 1: Basic flow (Default mode)")
    app = ApplicationProtocol("test_client")
    app.set_mode(Mode.DEFAULT)
    
    #send HELLO
    hello = app.send_hello()
    hello_data = app.prepare_message(hello)
    print(f"HELLO data: {hello_data}")
    
    #parse HELLO
    hello_parsed = app.parse_message(hello_data)
    print(f"Parsed: {hello_parsed}\n")
    
    #test 2: with encryption
    print("Test 2: Secure mode")
    app_secure = ApplicationProtocol("secure_client")
    app_secure.set_mode(Mode.SECURE)
    
    msg = app_secure.send_message("This is a secret!")
    msg_data = app_secure.prepare_message(msg)
    print(f"Encrypted MSG: {msg_data.hex()[:60]}...")
    
    msg_parsed = app_secure.parse_message(msg_data)
    text = app_secure.handle_message(msg_parsed)
    print(f"Decrypted text: {text}\n")
    
    #test 3: state machine
    print("Test 3: State machine")
    print(f"Initial state: {app.state}")
    app.send_hello()
    print(f"After HELLO: {app.state}")
    app.state = ConnectionState.CONNECTED
    app.send_mode_select(Mode.DEFAULT)
    print(f"After MODE_SELECT: {app.state}")
    app.state = ConnectionState.READY
    print(f"Ready: {app.state}")