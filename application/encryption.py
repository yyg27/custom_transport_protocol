from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os
import base64

class AESEncryption:
    def __init__(self, key: bytes = None):
        ##key is 16 bytes for AES-128
        if key is None:
            self.key = os.urandom(16)  #128-bit key
        else:
            if len(key) != 16:
                raise ValueError("Key must be 16 bytes for AES-128")
            self.key = key
    
    def encrypt(self, plaintext: bytes) -> bytes:
        #generate random IV
        iv = os.urandom(16)
        
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        
        #encrypt
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        return iv + ciphertext
    
    def decrypt(self, data: bytes) -> bytes:

        if len(data) < 16:
            raise ValueError("Data too short (need at least IV)")
        
        iv = data[:16]
        ciphertext = data[16:]
        
        #decrypt
        cipher = Cipher(
            algorithms.AES(self.key),
            modes.CBC(iv),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        return plaintext
    
    def get_key_b64(self) -> str:
        return base64.b64encode(self.key).decode('utf-8')
    
    @staticmethod
    def from_key_b64(key_b64: str):
        key = base64.b64decode(key_b64.encode('utf-8'))
        return AESEncryption(key)


class SimpleXOR:
    
    def __init__(self, key: bytes = b'secretkey'):
        self.key = key
    
    def xor(self, data: bytes) -> bytes:
        result = bytearray()
        key_len = len(self.key)
        
        for i, byte in enumerate(data):
            result.append(byte ^ self.key[i % key_len])
        
        return bytes(result)
    
    def encrypt(self, data: bytes) -> bytes:
        return self.xor(data)
    
    def decrypt(self, data: bytes) -> bytes:
        return self.xor(data)


#test code
if __name__ == "__main__":
    print("### Encryption Tests ###\n")
    
    #test1
    print("Test 1: AES-128-CBC")
    aes = AESEncryption()
    print(f"Key (base64): {aes.get_key_b64()}")
    
    plaintext = b"Hello, this is a secret message!"
    print(f"Plaintext: {plaintext}")
    
    encrypted = aes.encrypt(plaintext)
    print(f"Encrypted ({len(encrypted)} bytes): {encrypted.hex()[:60]}...")
    
    decrypted = aes.decrypt(encrypted)
    print(f"Decrypted: {decrypted}")
    print(f"Match: {plaintext == decrypted}\n")
    
    #test2
    print("Test 2: Key sharing")
    key_str = aes.get_key_b64()
    aes2 = AESEncryption.from_key_b64(key_str)
    
    encrypted2 = aes2.encrypt(b"Another message")
    decrypted2 = aes.decrypt(encrypted2)
    print(f"Cross-decrypt: {decrypted2}\n")
    
    #test3
    print("Test 3: XOR obfuscation")
    xor = SimpleXOR(b"mykey123")
    
    data = b"This is XOR test"
    print(f"Original: {data}")
    
    xor_encrypted = xor.encrypt(data)
    print(f"XOR encrypted: {xor_encrypted.hex()}")
    
    xor_decrypted = xor.decrypt(xor_encrypted)
    print(f"XOR decrypted: {xor_decrypted}")
    print(f"Match: {data == xor_decrypted}")