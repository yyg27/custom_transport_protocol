import json
from enum import Enum

class MessageType(Enum):
    """Application message types"""
    HELLO = "HELLO"           #initial connection
    MODE_SELECT = "MODE_SEL"  #select mode
    MSG = "MSG"               #chat message
    ACK_MSG = "ACK_MSG"       #message acknowledgment
    ERROR = "ERROR"           #error message
    BYE = "BYE"               #disconnect


class AppMessage:
    
    def __init__(self, msg_type: MessageType, payload: dict = None):

        self.msg_type = msg_type
        self.payload = payload or {}
    
    def to_bytes(self) -> bytes:
        ##JSON format
        data = {
            'type': self.msg_type.value,
            'payload': self.payload
        }
        return json.dumps(data).encode('utf-8')
    
    @staticmethod
    def from_bytes(data: bytes):
        try:
            obj = json.loads(data.decode('utf-8'))
            msg_type = MessageType(obj['type'])
            payload = obj.get('payload', {})
            return AppMessage(msg_type, payload)
        except Exception as e:
            raise ValueError(f"Failed to parse message: {e}")
    
    def __str__(self):
        return f"AppMessage({self.msg_type.value}, {self.payload})"


#helper functions for creating specific message types

def create_hello_message(client_id: str) -> AppMessage:
    return AppMessage(MessageType.HELLO, {
        'client_id': client_id,
        'version': '1.0'
    })


def create_mode_select_message(mode: str) -> AppMessage:
    return AppMessage(MessageType.MODE_SELECT, {
        'mode': mode
    })


def create_msg_message(text: str, sender: str = None) -> AppMessage:
    payload = {'text': text}
    if sender:
        payload['sender'] = sender
    return AppMessage(MessageType.MSG, payload)


def create_ack_message(msg_id: str = None) -> AppMessage:
    return AppMessage(MessageType.ACK_MSG, {
        'msg_id': msg_id
    })


def create_error_message(error_code: str, description: str) -> AppMessage:
    return AppMessage(MessageType.ERROR, {
        'code': error_code,
        'description': description
    })


def create_bye_message(reason: str = None) -> AppMessage:
    payload = {}
    if reason:
        payload['reason'] = reason
    return AppMessage(MessageType.BYE, payload)


#test code
if __name__ == "__main__":
    print("### Application Messages Test ###\n")
    
    #test 1: HELLO message
    print("Test 1: HELLO")
    hello = create_hello_message("client_123")
    print(f"Created: {hello}")
    hello_bytes = hello.to_bytes()
    print(f"Serialized: {hello_bytes}")
    hello_parsed = AppMessage.from_bytes(hello_bytes)
    print(f"Deserialized: {hello_parsed}\n")
    
    #test 2: MODE_SELECT
    print("Test 2: MODE_SELECT")
    mode_sel = create_mode_select_message("secure_obfs")
    print(f"Created: {mode_sel}")
    print(f"Bytes: {mode_sel.to_bytes()}\n")
    
    #test 3: MSG
    print("Test 3: MSG")
    msg = create_msg_message("Hello, World!", sender="Alice")
    print(f"Created: {msg}")
    msg_bytes = msg.to_bytes()
    print(f"Serialized: {msg_bytes}")
    msg_parsed = AppMessage.from_bytes(msg_bytes)
    print(f"Deserialized: {msg_parsed}\n")
    
    #test 4: ERROR
    print("Test 4: ERROR")
    err = create_error_message("INVALID_MODE", "Mode 'xyz' is not supported")
    print(f"Created: {err}")
    print(f"Bytes: {err.to_bytes()}\n")
    
    #test 5: BYE
    print("Test 5: BYE")
    bye = create_bye_message("User logout")
    print(f"Created: {bye}")