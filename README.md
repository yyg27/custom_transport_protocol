
# Custom Transport & Secure Application Protocol

### Project Overview

This project implements a complete networking stack from scratch, featuring:

-   **Custom Transport Layer Protocol**: A reliable data transfer protocol with custom header format, stop-and-wait ARQ mechanism, sequence numbers, acknowledgments, and Internet Checksum (RFC 1071) for error detection.
-   **Custom Application Layer Protocol**: A messaging protocol with multiple message types (HELLO, MSG, MODE_SELECT, etc.), state machine for connection management, and support for four different communication modes.
-   **Security Features**: AES-128 encryption in CBC mode for secure communications, with automatic key exchange between client and server.
-   **OBFS (Obfuscation) Support**: HTTPS-based carrier layer that tunnels custom protocol packets through HTTP/HTTPS requests, making network traffic appear as regular web traffic.
-   **Four Communication Modes**:
    1.  **Default Mode**: Direct UDP transport, no encryption
    2.  **Secure Mode**: Direct UDP transport with AES-128 encryption
    3.  **OBFS Mode**: HTTPS carrier without encryption
    4.  **Secure OBFS Mode**: HTTPS carrier with AES-128 encryption (maximum security)

The system follows strict layered architecture with clear separation between Application Layer, Transport Layer, and Carrier Layer, ensuring modularity and maintainability.

----------

## Project Structure

  

```

custom_transport_protocol/

├── transport/ # Custom Transport Layer

│ ├── __init__.py

│ ├── header.py # Custom header (14 bytes)

│ ├── checksum.py # Internet checksum (RFC 1071)

│ └── protocol.py # Stop-and-Wait ARQ

│

├── application/ # Application Layer Protocol

│ ├── __init__.py

│ ├── messages.py # Message types (HELLO, MSG, etc.)

│ ├── encryption.py # AES-128 encryption

│ └── protocol.py # State machine & mode handling

│

├── carrier/ # Carrier Layer

│ ├── __init__.py

│ ├── direct.py # Direct UDP/TCP

│ └── https_carrier.py # HTTPS carrier (OBFS modes)

│

├── server.py # Server application

├── client.py # Client application

├── config.py # Configuration

├── requirements.txt # Python dependencies

└── README.md # This file

  

```

  

----------

  

## Installation

  

### 1. Install Python 3.8+

  

Make sure you have Python 3.8 or higher installed:

  

```bash

python3  --version

  

```

  

### 2. Install Dependencies

  

```bash

pip  install  -r  requirements.txt

  

```

  

Or install manually:

  

```bash

pip  install  cryptography  requests  flask

  

```

  

----------

  

## Running the Application

  

-  **Default mode** - No encryption, direct transport

-  **Secure mode** - AES-128 encryption, direct transport

-  **OBFS mode** - No encryption, HTTPS carrier

-  **Secure OBFS mode** - AES-128 encryption + HTTPS carrier

  

----------

  

## Usage Examples

  

### Test 1: Default Mode (No Encryption)

  

**Terminal 1 - Start Server:**

  

```bash

python  server.py  --port  5000  --mode  default

  

```

  

**Terminal 2 - Start Client:**

  

```bash

python  client.py  --host  127.0.0.1  --port  5000  --mode  default

  

```

  

Then type messages in the client terminal!

  

----------

  

### Test 2: Secure Mode (With AES-128 Encryption)

  

**Terminal 1 - Start Server:**

  

```bash

python  server.py  --port  5000  --mode  secure

  

```

  

**Terminal 2 - Start Client:**

  

```bash

python  client.py  --host  127.0.0.1  --port  5000  --mode  secure

  

```

  

You'll see the encryption key in the server logs. Client and server automatically share the key.

  

----------

  

### Test 3: OBFS Mode (HTTPS Carrier, No Encryption)

  

**Step 1 - Start Server:**

  

```bash

python  server.py  --mode  obfs

  

```

  

**Step 2 - Start Client:**

  

```bash

python  client.py  --host  127.0.0.1  --mode  obfs

  

```

  

Packets are now tunneled through HTTPS!

  

----------

  

### Test 4: Secure OBFS Mode (HTTPS + Encryption)

  

**Terminal 1 - Start Server:**

  

```bash

python  server.py  --mode  secure_obfs

  

```

  

**Terminal 2 - Start Client:**

  

```bash

python  client.py  --host  127.0.0.1  --mode  secure_obfs

  

```

  

Maximum security: Encrypted data over HTTPS!

  

----------

  

### Test 5: Testing Transport Layer Directly

  

You can test the transport protocol independently:

  

**Terminal 1:**

  

```bash

python  -m  transport.protocol  server  5000

  

```

  

**Terminal 2:**

  

```bash

python  -m  transport.protocol  client  127.0.0.1  5000

  

```

  

----------

  

### Test 5: Testing Transport Layer Directly

  

You can test the transport protocol independently:

  

**Terminal 1:**

  

```bash

python  -m  transport.protocol  server  5000

  

```

  

**Terminal 2:**

  

```bash

python  -m  transport.protocol  client  127.0.0.1  5000

  

```

  

----------

  

### Test 6: Testing Carrier Layers

  

**Test HTTPS Carrier:**

  

Terminal 1:

  

```bash

python  -m  carrier.https_carrier  server

  

```

  

Terminal 2:

  

```bash

python  -m  carrier.https_carrier  client

  

```

  

----------

  

### Test 7: Testing Individual Modules

  

**Test header:**

  

```bash

python  -m  transport.header

  

```

  

**Test checksum:**

  

```bash

python  -m  transport.checksum

  

```

  

**Test messages:**

  

```bash

python  -m  application.messages

  

```

  

**Test encryption:**

  

```bash

python  -m  application.encryption

  

```

  

----------

  

## Configuration

  

Edit `config.py` to change:

  

- Default ports

- Timeout values

- Buffer sizes

- Logging level

- Encryption settings

  

----------

  

## Protocol Specifications

  

### Transport Layer Header (14 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Version (1B) |   Flags (1B)  |     Sequence Number (4B)      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Acknowledgment Number (4B)                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Payload Length (2B)        |         Checksum (2B)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

```

  

**Flags:**

  

-  `0x01` - DATA

-  `0x02` - ACK

-  `0x04` - SYN (connection start)

-  `0x08` - FIN (connection end)

  

### Application Layer Messages

  

Message types:

  

-  `HELLO` - Initial connection handshake

-  `MODE_SELECT` - Mode negotiation

-  `MSG` - Chat message

-  `ACK_MSG` - Message acknowledgment

-  `ERROR` - Error message

-  `BYE` - Disconnect

  

All messages are JSON-encoded:

  

```json

{

"type": "MSG",

"payload": {

"text": "Hello, World!",

"sender": "client_123"

}

}

  

```

  

### Reliability Mechanism

  

**Stop-and-Wait ARQ:**

  

1. Sender transmits packet with sequence number N

2. Sender waits for ACK(N+1)

3. If timeout occurs, retransmit packet

4. Receiver sends ACK only for correctly received packets

5. Duplicate packets are discarded

  

**Error Detection:**

  

- Internet Checksum (RFC 1071) over header + payload

- Corrupted packets are discarded

- Sender retransmits on timeout

  

----------

  

## References

  

- RFC 1071 - Internet Checksum

- Stop-and-Wait ARQ

- AES-128 CBC mode encryption

- Python cryptography library

  

----------

  

## Troubleshooting

  

**Problem:** "Address already in use"

  

```bash

# Kill process using the port

lsof  -ti:5000 | xargs  kill  -9

  

```

  

**Problem:** "Module not found"

  

```bash

# Make sure you're in the project root directory

# And have installed requirements

pip  install  -r  requirements.txt

  

```

  

**Problem:** Client can't connect

  

- Check firewall settings

- Make sure server is running first

- Verify IP address and port

  

----------
