#!/usr/bin/env python3

import socket
import sys
import logging
import time
from threading import Thread

from transport import TransportProtocol
from application import (
    ApplicationProtocol, Mode, ConnectionState
)
from carrier import DirectCarrier, HTTPSCarrier
import config

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class MessagingClient:
    def __init__(self, server_ip, server_port, mode=Mode.DEFAULT):
        self.server_ip = server_ip
        self.server_port = server_port
        self.mode = mode
        self.sock = None
        self.tp = TransportProtocol(timeout=config.TIMEOUT, max_retries=config.MAX_RETRIES)
        self.app = ApplicationProtocol(client_id=f"client_{int(time.time())}")
        self.connected = False
        
        #carrier layer
        self.carrier = None
        self.use_https = mode in [Mode.OBFS, Mode.SECURE_OBFS]
        
        if self.use_https:
            #HTTPS mode
            https_port = getattr(config, 'HTTPS_PORT', 5443)
            server_url = f"https://{server_ip}:{https_port}/api/data"
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            self.carrier = HTTPSCarrier(mode='client', server_url=server_url)
        else:
            #direct UDP mode
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.carrier = DirectCarrier(self.sock)
        
    def connect(self):
        try:
            logger.info(f"Connecting to {self.server_ip}:{self.server_port}...")
            
            #send HELLO
            hello_msg = self.app.send_hello()
            hello_data = self.app.prepare_message(hello_msg)
            
            if self.use_https:
                success = self.carrier.send(hello_data)
            else:
                success = self.tp.tp_send(self.sock, hello_data, 
                                         (self.server_ip, self.server_port))
            
            if not success:
                logger.error("Failed to send HELLO")
                return False
            
            if self.use_https:
                result = self.carrier.recv(timeout=5.0)
            else:
                result = self.tp.tp_recv(self.sock, buffer_size=config.BUFFER_SIZE)
            
            if not result or result[0] is None:
                logger.error("No response to HELLO")
                return False
            
            ack_payload, _ = result
            ack_msg = self.app.parse_message(ack_payload)
            logger.info("HELLO acknowledged")
            
            #send MODE_SELECT
            self.app.state = ConnectionState.CONNECTED
            mode_msg = self.app.send_mode_select(self.mode)
            mode_data = self.app.prepare_message(mode_msg)
            
            if self.use_https:
                success = self.carrier.send(mode_data)
            else:
                success = self.tp.tp_send(self.sock, mode_data,
                                         (self.server_ip, self.server_port))
            
            if not success:
                logger.error("Failed to send MODE_SELECT")
                return False
            
            if self.use_https:
                result = self.carrier.recv(timeout=5.0)
            else:
                result = self.tp.tp_recv(self.sock, buffer_size=config.BUFFER_SIZE)
            
            if not result or result[0] is None:
                logger.error("No response to MODE_SELECT")
                return False
            
            ack_payload, _ = result
            ack_msg = self.app.parse_message(ack_payload)
            logger.info(f"Mode {self.mode.value} negotiated")
            
            self.app.state = ConnectionState.READY
            self.connected = True
            
            logger.info(f"=" * 60)
            logger.info(f"Connected successfully!")
            logger.info(f"Mode: {self.mode.value.upper()}")
            if self.mode in [Mode.SECURE, Mode.SECURE_OBFS]:
                logger.info(f"Encryption enabled (AES-128)")
            if self.use_https:
                logger.info(f"Carrier: HTTPS (OBFS mode)")
            else:
                logger.info(f"Carrier: Direct UDP")
            logger.info(f"=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def send_message(self, text: str):
        if not self.connected:
            logger.error("Not connected to server")
            return False
        
        try:
            msg = self.app.send_message(text)
            msg_data = self.app.prepare_message(msg)
            
            if self.use_https:
                success = self.carrier.send(msg_data)
            else:
                success = self.tp.tp_send(self.sock, msg_data,
                                         (self.server_ip, self.server_port))
            
            if success:
                if self.use_https:
                    result = self.carrier.recv(timeout=5.0)
                else:
                    result = self.tp.tp_recv(self.sock, buffer_size=config.BUFFER_SIZE)
                
                if result and result[0]:
                    logger.debug("Message acknowledged by server")
                return True
            else:
                logger.error("Failed to send message")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def run(self):
        if not self.connect():
            logger.error("Connection failed, exiting")
            sys.exit(1)
        
        print("\nType your messages (or 'quit' to exit):")
        print("-" * 60)
        
        try:
            while True:
                try:
                    text = input(">>> ")
                    
                    if text.lower() in ['quit', 'exit', 'bye']:
                        logger.info("Disconnecting...")
                        break
                    
                    if text.strip():
                        success = self.send_message(text)
                        if success:
                            print("✓ Sent")
                        else:
                            print("✗ Failed")
                
                except EOFError:
                    break
                    
        except KeyboardInterrupt:
            logger.info("\nDisconnecting...")
        
        self.disconnect()
    
    def disconnect(self):
        try:
            if self.connected:
                bye_msg = self.app.send_bye()
                bye_data = self.app.prepare_message(bye_msg)
                
                if self.use_https:
                    self.carrier.send(bye_data)
                else:
                    self.tp.tp_send(self.sock, bye_data,
                                   (self.server_ip, self.server_port))
            
            if self.carrier:
                self.carrier.close()
            if self.sock:
                self.sock.close()
            
            logger.info("Disconnected")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Messaging Client')
    parser.add_argument('--host', default=config.DEFAULT_SERVER_IP,
                       help='Server IP address')
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
    
    client = MessagingClient(args.host, args.port, mode)
    client.run()


if __name__ == '__main__':
    main()