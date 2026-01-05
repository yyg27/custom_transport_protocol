import socket
import time
import logging
from typing import Tuple, Optional

from transport.header import (
    TransportHeader, HEADER_SIZE, FLAG_DATA, FLAG_ACK,
    create_data_packet, create_ack_packet
)
from transport.checksum import add_checksum, verify_packet

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransportProtocol:
    
    def __init__(self, timeout=2.0, max_retries=5):
        self.timeout = timeout
        self.max_retries = max_retries
        self.seq_num = 0
        self.expected_seq = 0
        
    def tp_send(self, sock: socket.socket, data: bytes, dest_addr: Tuple[str, int]) -> bool:
        header = create_data_packet(self.seq_num, data)
        header = add_checksum(header, data)
        
        packet = header.pack() + data
        
        logger.info(f"[SEND] Seq={self.seq_num}, Size={len(data)} bytes")
        
        for attempt in range(self.max_retries):
            try:
                sock.sendto(packet, dest_addr)
                logger.debug(f"[SEND] Attempt {attempt + 1}/{self.max_retries}")
                
                sock.settimeout(self.timeout)
                
                start_time = time.time()
                while time.time() - start_time < self.timeout:
                    try:
                        ack_data, addr = sock.recvfrom(HEADER_SIZE)
                        
                        ack_header = TransportHeader.unpack(ack_data)
                        
                        if ack_header.has_flag(FLAG_ACK) and ack_header.ack_num == self.seq_num + 1:
                            logger.info(f"[RECV] ACK for Seq={self.seq_num} ✓")
                            self.seq_num += 1
                            return True
                        else:
                            logger.debug(f"[RECV] Wrong ACK: expected {self.seq_num + 1}, got {ack_header.ack_num}")
                    
                    except socket.timeout:
                        break
                
                logger.warning(f"[TIMEOUT] No ACK for Seq={self.seq_num}, retrying...")
            
            except Exception as e:
                logger.error(f"[ERROR] Send failed: {e}")
                return False
        
        logger.error(f"[FAILED] Max retries exceeded for Seq={self.seq_num}")
        return False
    
    def tp_recv(self, sock: socket.socket, buffer_size=4096) -> Optional[Tuple[bytes, Tuple[str, int]]]:
        try:
            packet, addr = sock.recvfrom(buffer_size)
            
            if len(packet) < HEADER_SIZE:
                logger.warning("[RECV] Packet too short, discarding")
                return None
            
            header_bytes = packet[:HEADER_SIZE]
            payload = packet[HEADER_SIZE:]
            
            header = TransportHeader.unpack(header_bytes)
            
            is_valid, msg = header.validate()
            if not is_valid:
                logger.warning(f"[RECV] Invalid header: {msg}")
                return None
            
            is_valid, msg = verify_packet(header_bytes, payload)
            if not is_valid:
                logger.warning(f"[RECV] {msg}, discarding packet")
                return None
            
            if not header.has_flag(FLAG_DATA):
                logger.debug(f"[RECV] Not a DATA packet, ignoring")
                return None
            
            logger.info(f"[RECV] Seq={header.seq_num}, Size={len(payload)} bytes")
            
            if header.seq_num == self.expected_seq:
                ack_header = create_ack_packet(ack_num=header.seq_num + 1)
                ack_packet = ack_header.pack()
                
                sock.sendto(ack_packet, addr)
                logger.info(f"[SEND] ACK for Seq={header.seq_num}")
                
                self.expected_seq += 1
                return payload, addr
            
            elif header.seq_num < self.expected_seq:
                logger.warning(f"[RECV] Duplicate Seq={header.seq_num}, re-ACKing")
                ack_header = create_ack_packet(ack_num=header.seq_num + 1)
                ack_packet = ack_header.pack()
                sock.sendto(ack_packet, addr)
                return None
            
            else:
                logger.warning(f"[RECV] Out of order: expected {self.expected_seq}, got {header.seq_num}")
                return None
        
        except socket.timeout:
            return None
        except Exception as e:
            logger.error(f"[ERROR] Receive failed: {e}")
            return None
    
    def reset(self):
        self.seq_num = 0
        self.expected_seq = 0


#test code
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Server: python protocol.py server [port]")
        print("  Client: python protocol.py client [server_ip] [server_port]")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == "server":
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
        
        print(f"Starting server on port {port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', port))
        
        tp = TransportProtocol()
        
        print("Waiting for messages... (Ctrl+C to stop)")
        try:
            while True:
                result = tp.tp_recv(sock)
                if result:
                    payload, addr = result
                    print(f"\n>>> Received from {addr}: {payload.decode('utf-8', errors='ignore')}")
        except KeyboardInterrupt:
            print("\nServer stopped")
    
    elif mode == "client":
        server_ip = sys.argv[2] if len(sys.argv) > 2 else '127.0.0.1'
        server_port = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
        
        print(f"Connecting to {server_ip}:{server_port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        tp = TransportProtocol()
        
        print("Enter messages (Ctrl+C to stop):")
        try:
            while True:
                msg = input(">>> ")
                if msg:
                    data = msg.encode('utf-8')
                    success = tp.tp_send(sock, data, (server_ip, server_port))
                    if success:
                        print("Message sent successfully")
                    else:
                        print("Failed to send message")
        except KeyboardInterrupt:
            print("\nClient stopped")
    
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)