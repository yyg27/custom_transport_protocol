import socket
import logging

logger = logging.getLogger(__name__)


class DirectCarrier:
    
    def __init__(self, sock=None):

        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.owns_socket = True
        else:
            self.sock = sock
            self.owns_socket = False
    
    def send(self, data: bytes, dest_addr: tuple) -> bool:
        try:
            self.sock.sendto(data, dest_addr)
            logger.debug(f"[DirectCarrier] Sent {len(data)} bytes to {dest_addr}")
            return True
        except Exception as e:
            logger.error(f"[DirectCarrier] Send failed: {e}")
            return False
    
    def recv(self, buffer_size=4096) -> tuple:
        try:
            data, addr = self.sock.recvfrom(buffer_size)
            logger.debug(f"[DirectCarrier] Received {len(data)} bytes from {addr}")
            return data, addr
        except socket.timeout:
            return None, None
        except Exception as e:
            logger.error(f"[DirectCarrier] Receive failed: {e}")
            return None, None
    
    def bind(self, addr: tuple):
        self.sock.bind(addr)
        logger.info(f"[DirectCarrier] Bound to {addr}")
    
    def set_timeout(self, timeout: float):
        self.sock.settimeout(timeout)
    
    def close(self):
        if self.owns_socket and self.sock:
            self.sock.close()
            logger.debug("[DirectCarrier] Socket closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


#test
if __name__ == "__main__":
    import time
    
    print("### Direct Carrier Test ###\n")
    
    #test server
    def test_server():
        carrier = DirectCarrier()
        carrier.bind(('', 5555))
        carrier.set_timeout(5.0)
        
        print("Server listening on port 5555...")
        data, addr = carrier.recv()
        
        if data:
            print(f"Received: {data.decode()}")
            carrier.send(b"ACK", addr)
        
        carrier.close()
    
    #test client
    def test_client():
        time.sleep(0.5)
        
        carrier = DirectCarrier()
        carrier.set_timeout(2.0)
        
        print("Client sending message...")
        carrier.send(b"Hello Server!", ('127.0.0.1', 5555))
        
        data, addr = carrier.recv()
        if data:
            print(f"Received ACK: {data.decode()}")
        
        carrier.close()
    
    #run tests
    from threading import Thread
    
    server_thread = Thread(target=test_server)
    client_thread = Thread(target=test_client)
    
    server_thread.start()
    client_thread.start()
    
    server_thread.join()
    client_thread.join()
    
    print("\n Direct Carrier test complete")