import base64
import json
import logging
import threading
import time
from queue import Queue, Empty
from typing import Optional, Tuple

import requests
from flask import Flask, request, jsonify
from werkzeug.serving import make_server

logger = logging.getLogger(__name__)


class HTTPSCarrier:

    def __init__(self, mode='client', server_url=None):
        
        self.mode = mode
        self.server_url = server_url
        self.recv_queue = Queue()
        self.running = False
        
        #for server mode
        self.app = None
        self.server_thread = None
        self.flask_server = None
        
        if mode == 'client' and not server_url:
            raise ValueError("Client mode requires server_url")
    
    def send(self, data: bytes, dest_addr: tuple = None) -> bool:
        if self.mode != 'client':
            logger.error("[HTTPSCarrier] Send only available in client mode")
            return False
        
        try:
            #encode data as base64
            encoded = base64.b64encode(data).decode('utf-8')
            
            payload = {
                'data': encoded,
                'timestamp': time.time()
            }
            
            #POST request
            response = requests.post(
                self.server_url,
                json=payload,
                timeout=5.0,
                verify=False
            )
            
            if response.status_code == 200:
                logger.debug(f"[HTTPSCarrier] Sent {len(data)} bytes via HTTPS")
                
                resp_data = response.json()
                if resp_data.get('has_data'):
                    server_data = base64.b64decode(resp_data['data'])
                    self.recv_queue.put((server_data, ('server', 0)))
                
                return True
            else:
                logger.error(f"[HTTPSCarrier] Server returned {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"[HTTPSCarrier] Send failed: {e}")
            return False
    
    def recv(self, buffer_size=4096, timeout=None) -> Tuple[Optional[bytes], Optional[tuple]]:
        try:
            data, addr = self.recv_queue.get(timeout=timeout)
            logger.debug(f"[HTTPSCarrier] Received {len(data)} bytes")
            return data, addr
        except Empty:
            return None, None
    
    def start_server(self, host='0.0.0.0', port=5443, certfile=None, keyfile=None):
        if self.mode != 'server':
            raise RuntimeError("start_server() only for server mode")
        
        self.app = Flask(__name__)
        self.app.logger.setLevel(logging.ERROR)  # Suppress Flask logs
        
        self.client_queues = {}
        
        #API endpoint
        @self.app.route('/api/data', methods=['POST'])
        def receive_data():
            try:
                client_ip = request.remote_addr
                client_addr = (client_ip, 0)
                
                data = request.get_json()
                encoded = data.get('data')
                
                if not encoded:
                    return jsonify({'error': 'No data'}), 400
                
                packet_data = base64.b64decode(encoded)
                
                logger.debug(f"[HTTPSCarrier] Received {len(packet_data)} bytes from {client_ip}")
                
                self.recv_queue.put((packet_data, client_addr))
                
                response = {
                    'status': 'ok',
                    'has_data': False
                }
                
                return jsonify(response), 200
                
            except Exception as e:
                logger.error(f"[HTTPSCarrier] Error handling request: {e}")
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/health', methods=['GET'])
        def health():
            return jsonify({'status': 'ok'}), 200
        
        ssl_context = None
        if certfile and keyfile:
            ssl_context = (certfile, keyfile)
        
        self.flask_server = make_server(host, port, self.app, ssl_context=ssl_context)
        
        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        
        logger.info(f"[HTTPSCarrier] HTTPS server started on {host}:{port}")
    
    def _run_server(self):
        self.flask_server.serve_forever()
    
    def stop_server(self):
        if self.flask_server:
            self.flask_server.shutdown()
            self.running = False
            logger.info("[HTTPSCarrier] HTTPS server stopped")
    
    def close(self):
        if self.mode == 'server':
            self.stop_server()


#test
if __name__ == "__main__":
    import sys
    
    def test_server():
        print("Starting HTTPS server on port 5443...")
        
        carrier = HTTPSCarrier(mode='server')
        carrier.start_server(host='127.0.0.1', port=5443)
        
        print("Server ready. Waiting for data...")
        
        #receive data
        data, addr = carrier.recv(timeout=10.0)
        
        if data:
            print(f"Received from {addr}: {data.decode('utf-8', errors='ignore')}")
        else:
            print("No data received (timeout)")
        
        carrier.stop_server()
        print("Server stopped")
    
    def test_client():
        time.sleep(1)
        
        print("\nClient: Sending data via HTTPS...")
        
        carrier = HTTPSCarrier(mode='client', server_url='http://127.0.0.1:5443/api/data')
        
        test_data = b"Hello via HTTPS!"
        success = carrier.send(test_data)
        
        if success:
            print("Data sent successfully")
        else:
            print("Failed to send data")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Server: python https_carrier.py server")
        print("  Client: python https_carrier.py client")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == 'server':
        test_server()
    elif mode == 'client':
        test_client()
    else:
        print(f"Unknown mode: {mode}")