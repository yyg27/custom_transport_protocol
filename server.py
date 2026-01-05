#!/usr/bin/env python3

import socket
import sys
import logging
from threading import Thread

from transport import TransportProtocol
from application import (
    ApplicationProtocol, Mode, MessageType,
    create_ack_message
)
from carrier import DirectCarrier, HTTPSCarrier
import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class MessagingServer:
    def __init__(self, host='', port=5000, mode=Mode.DEFAULT):
        self.host = host
        self.port = port
        self.mode = mode
        self.sock = None
        self.tp = TransportProtocol(timeout=config.TIMEOUT, max_retries=config.MAX_RETRIES)
        self.app = ApplicationProtocol(client_id=config.SERVER_ID)
        self.app.set_mode(mode)
        self.running = False
        self.clients = {}  #addr -> app_protocol
        
        #carrier layer
        self.carrier = None
        self.use_https = mode in [Mode.OBFS, Mode.SECURE_OBFS]
        
    def start(self):
        try:
            if self.use_https:
                #HTTPS mode
                logger.info("Starting in OBFS mode (HTTPS carrier)")
                self.carrier = HTTPSCarrier(mode='server')
                
                #use HTTPS port
                https_port = getattr(config, 'HTTPS_PORT', 5443)
                cert_file = getattr(config, 'HTTPS_CERT_FILE', 'server.crt')
                key_file = getattr(config, 'HTTPS_KEY_FILE', 'server.key')
                
                #check if cert files exist (probs do not exist)//todo
                import os
                if not os.path.exists(cert_file) or not os.path.exists(key_file):
                    logger.warning("SSL certificate not found! Starting without HTTPS...")
                    logger.info("Starting with HTTP (not HTTPS) for testing...")
                    self.carrier.start_server(host=self.host, port=https_port)
                else:
                    self.carrier.start_server(host=self.host, port=https_port, 
                                            certfile=cert_file, keyfile=key_file)
                
                self.port = https_port
            else:
                #direct UDP mode
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.sock.bind((self.host, self.port))
                self.carrier = DirectCarrier(self.sock)
            
            self.running = True
            
            logger.info(f"=" * 60)
            logger.info(f"Server started on {self.host}:{self.port}")
            logger.info(f"Mode: {self.mode.value.upper()}")
            if self.mode in [Mode.SECURE, Mode.SECURE_OBFS]:
                logger.info(f"Encryption key: {self.app.encryption.get_key_b64()}")
            if self.use_https:
                logger.info(f"Carrier: HTTPS (OBFS mode)")
            else:
                logger.info(f"Carrier: Direct UDP")
            logger.info(f"=" * 60)
            logger.info("Waiting for clients... (Ctrl+C to stop)")
            
            self.listen()
            
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            sys.exit(1)
    
    def listen(self):
        while self.running:
            try:
                #receive transport packet (via carrier)
                if self.use_https:
                    result = self.carrier.recv(timeout=1.0)
                    if result[0] is None:
                        continue
                    payload, addr = result
                else:
                    result = self.tp.tp_recv(self.sock, buffer_size=config.BUFFER_SIZE)
                    if not result:
                        continue
                    payload, addr = result
                
                self.handle_message(payload, addr)
                    
            except KeyboardInterrupt:
                logger.info("\nShutting down server...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
    
    def handle_message(self, payload: bytes, addr):
        try:
            #get or create app protocol for this client
            if addr not in self.clients:
                logger.info(f"New client: {addr}")
                client_app = ApplicationProtocol(client_id=f"client_{addr[1]}")
                client_app.set_mode(self.mode)
                
                #share encryption key if secure mode
                if self.mode in [Mode.SECURE, Mode.SECURE_OBFS]:
                    client_app.set_encryption_key(self.app.encryption.get_key_b64())
                
                self.clients[addr] = client_app
            
            client_app = self.clients[addr]
            
            #parse application message
            app_msg = client_app.parse_message(payload)
            
            logger.info(f"[{addr}] Received: {app_msg.msg_type.value}")
            
            #handle different message types
            if app_msg.msg_type == MessageType.HELLO:
                #respond to HELLO
                response = client_app.handle_hello(app_msg)
                self.send_response(response, addr, client_app)
                
            elif app_msg.msg_type == MessageType.MODE_SELECT:
                #handle mode selection
                response = client_app.handle_mode_select(app_msg)
                self.send_response(response, addr, client_app)
                
            elif app_msg.msg_type == MessageType.MSG:
                #handle chat message
                text = client_app.handle_message(app_msg)
                print(f"\n>>> [{addr}]: {text}")
                
                #send ACK
                response = create_ack_message()
                self.send_response(response, addr, client_app)
                
            elif app_msg.msg_type == MessageType.BYE:
                logger.info(f"[{addr}] Client disconnected")
                if addr in self.clients:
                    del self.clients[addr]
            
        except Exception as e:
            logger.error(f"Error handling message from {addr}: {e}")
    
    def send_response(self, app_msg, addr, client_app):
        try:
            payload = client_app.prepare_message(app_msg)
            
            if self.use_https:
                logger.debug(f"[{addr}] Response prepared (HTTPS mode)")
                success = True
            else:
                success = self.tp.tp_send(self.sock, payload, addr)
            
            if success:
                logger.debug(f"[{addr}] Sent: {app_msg.msg_type.value}")
            else:
                logger.error(f"[{addr}] Failed to send response")
                
        except Exception as e:
            logger.error(f"Error sending response to {addr}: {e}")
    
    def stop(self):
        self.running = False
        if self.carrier:
            self.carrier.close()
        if self.sock:
            self.sock.close()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Messaging Server')
    parser.add_argument('--port', type=int, default=config.DEFAULT_SERVER_PORT,
                       help='Server port')
    parser.add_argument('--mode', choices=['default', 'secure', 'obfs', 'secure_obfs'], 
                       default='default',
                       help='Communication mode')
    
    args = parser.parse_args()
    
    #convert mode string to Mode enum
    mode_map = {
        'default': Mode.DEFAULT,
        'secure': Mode.SECURE,
        'obfs': Mode.OBFS,
        'secure_obfs': Mode.SECURE_OBFS
    }
    mode = mode_map[args.mode]
    
    server = MessagingServer(port=args.port, mode=mode)
    server.start()


if __name__ == '__main__':
    main()