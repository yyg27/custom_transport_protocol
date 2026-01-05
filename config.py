#network settings
DEFAULT_SERVER_IP = '127.0.0.1'
DEFAULT_SERVER_PORT = 5000
HTTPS_PORT = 5443  # For OBFS modes

#buffer sizes
BUFFER_SIZE = 4096
MAX_PAYLOAD_SIZE = 3072  # Leave room for headers

#transport protocol settings
TIMEOUT = 2.0  # seconds
MAX_RETRIES = 5

#logging
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR

#modes
MODES = {
    'default': 'Default mode (no encryption, no obfuscation)',
    'secure': 'Secure mode (encryption, no obfuscation)',
    'obfs': 'OBFS mode (no encryption, HTTPS obfuscation)',
    'secure_obfs': 'Secure OBFS mode (encryption + HTTPS obfuscation)'
}

#HTTPS settings (for OBFS modes)
HTTPS_CERT_FILE = 'server.crt'
HTTPS_KEY_FILE = 'server.key'
HTTPS_API_ENDPOINT = '/api/data'

#encryption
DEFAULT_XOR_KEY = b'networkproject2024'

#application
CLIENT_ID_PREFIX = 'client_'
SERVER_ID = 'server_main' 