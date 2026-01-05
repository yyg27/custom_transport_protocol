def calculate_checksum(data):
    #to make data lenght even
    if len(data) % 2 == 1:
        data += b'\x00'
    
    #sum all 16-bit words
    checksum = 0
    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        checksum += word
        
        #32-bit to 16-bit
        checksum = (checksum & 0xFFFF) + (checksum >> 16)
    
    #one's complement
    checksum = ~checksum & 0xFFFF
    
    return checksum


def verify_checksum(data, received_checksum):
    calculated = calculate_checksum(data)
    return calculated == received_checksum


def add_checksum(header, payload):
    #checksum to 0
    header.checksum = 0
    
    header_bytes = header.pack()
    
    data = header_bytes + payload
    checksum = calculate_checksum(data)
    
    header.checksum = checksum
    
    return header


def verify_packet(header_bytes, payload):
   
    from transport.header import TransportHeader, HEADER_SIZE
    
    if len(header_bytes) < HEADER_SIZE:
        return False, "Header too short"
    
    header = TransportHeader.unpack(header_bytes)
    received_checksum = header.checksum
    
    header.checksum = 0
    header_bytes_zeroed = header.pack()
    
    data = header_bytes_zeroed + payload
    calculated_checksum = calculate_checksum(data)
    
    if calculated_checksum == received_checksum:
        return True, "Checksum valid"
    else:
        return False, f"Checksum mismatch: expected {received_checksum}, got {calculated_checksum}"


#test code
if __name__ == "__main__":
    print("### Checksum Tests ###\n")
    
    #test 1: Basic checksum calculation
    print("Test 1: Basic calculation")
    test_data = b"Hello, World!"
    checksum = calculate_checksum(test_data)
    print(f"Data: {test_data}")
    print(f"Checksum: 0x{checksum:04x} ({checksum})\n")
    
    #test 2: Verify checksum
    print("Test 2: Verification")
    is_valid = verify_checksum(test_data, checksum)
    print(f"Valid: {is_valid}\n")
    
    #test 3: Corrupted data
    print("Test 3: Corrupted data")
    corrupted = b"Hello, Wrld!"  # Changed 'o' to nothing
    is_valid = verify_checksum(corrupted, checksum)
    print(f"Valid (should be False): {is_valid}\n")
    
    #test 4: With header
    print("Test 4: Header + Payload")
    from transport.header import create_data_packet
    
    payload = b"Test message"
    header = create_data_packet(seq_num=1, payload=payload)
    
    print(f"Before checksum: {header}")
    header = add_checksum(header, payload)
    print(f"After checksum: {header}")
    
    #verify
    header_bytes = header.pack()
    is_valid, msg = verify_packet(header_bytes, payload)
    print(f"Verification: {is_valid} - {msg}\n")
    
    #test 5: Corrupted payload
    print("Test 5: Corrupted payload")
    corrupted_payload = b"Txst message"  #typo
    is_valid, msg = verify_packet(header_bytes, corrupted_payload)
    print(f"Verification (should fail): {is_valid} - {msg}")