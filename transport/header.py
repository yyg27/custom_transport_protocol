import struct

#flags
FLAG_DATA = 0x01
FLAG_ACK = 0x02
FLAG_SYN = 0x04
FLAG_FIN = 0x08

PROTOCOL_VERSION = 1

#header format: !BBIHHI
#B = unsigned char (1 byte)
#I = unsigned int (4 bytes)
#H = unsigned short (2 bytes)
HEADER_FORMAT = '!BBIHHI'
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)  #14 bytes


class TransportHeader:
    
    def __init__(self, version=PROTOCOL_VERSION, flags=0, seq_num=0, 
                 ack_num=0, payload_length=0, checksum=0):
        self.version = version
        self.flags = flags
        self.seq_num = seq_num
        self.ack_num = ack_num
        self.payload_length = payload_length
        self.checksum = checksum
    
    def pack(self):
        return struct.pack(
            HEADER_FORMAT,
            self.version,
            self.flags,
            self.seq_num,
            self.ack_num,
            self.payload_length,
            self.checksum
        )
    
    @staticmethod
    def unpack(data):
        if len(data) < HEADER_SIZE:
            raise ValueError(f"Data too short: expected {HEADER_SIZE}, got {len(data)}")
        
        fields = struct.unpack(HEADER_FORMAT, data[:HEADER_SIZE])
        return TransportHeader(
            version=fields[0],
            flags=fields[1],
            seq_num=fields[2],
            ack_num=fields[3],
            payload_length=fields[4],
            checksum=fields[5]
        )
    
    def has_flag(self, flag):
        return bool(self.flags & flag)
    
    def set_flag(self, flag):
        self.flags |= flag
    
    def clear_flag(self, flag):
        self.flags &= ~flag
    
    def __str__(self):
        flag_str = []
        if self.has_flag(FLAG_DATA):
            flag_str.append("DATA")
        if self.has_flag(FLAG_ACK):
            flag_str.append("ACK")
        if self.has_flag(FLAG_SYN):
            flag_str.append("SYN")
        if self.has_flag(FLAG_FIN):
            flag_str.append("FIN")
        
        return (f"TransportHeader(ver={self.version}, "
                f"flags={self.flags}[{','.join(flag_str)}], "
                f"seq={self.seq_num}, ack={self.ack_num}, "
                f"len={self.payload_length}, checksum={self.checksum})")
    
    def validate(self):
        if self.version != PROTOCOL_VERSION:
            return False, f"Invalid protocol version: {self.version}"
        
        if self.payload_length < 0 or self.payload_length > 65535:
            return False, f"Invalid payload length: {self.payload_length}"
        
        return True, "OK"


def create_data_packet(seq_num, payload):
    header = TransportHeader(
        flags=FLAG_DATA,
        seq_num=seq_num,
        payload_length=len(payload)
    )
    return header


def create_ack_packet(ack_num):
    header = TransportHeader(
        flags=FLAG_ACK,
        ack_num=ack_num,
        payload_length=0
    )
    return header


#test code
if __name__ == "__main__":
    print(f"Header size: {HEADER_SIZE} bytes\n")
    
    #test 1: Create and pack a DATA packet
    print("### Test 1: DATA Packet ###")
    header = create_data_packet(seq_num=1, payload=b"Hello World")
    header.checksum = 0x1234  # Temporary, will calculate later
    
    print(f"Created: {header}")
    packed = header.pack()
    print(f"Packed: {packed.hex()}")
    print(f"Length: {len(packed)} bytes\n")
    
    #test 2: Unpack and verify
    print("### Test 2: Unpack ###")
    unpacked = TransportHeader.unpack(packed)
    print(f"Unpacked: {unpacked}")
    print(f"Validation: {unpacked.validate()}\n")
    
    #test 3: ACK packet
    print("### Test 3: ACK Packet ###")
    ack = create_ack_packet(ack_num=2)
    print(f"ACK: {ack}")