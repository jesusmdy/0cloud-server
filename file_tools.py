from cryptography.fernet import Fernet
import base64

def write_key():
    key = Fernet.generate_key()
    with open("files.key", "wb") as key_file:
        key_file.write(key)
        
def load_key():
    return open("files.key", "rb").read()

def encrypt_file(file_content, key):
    """
    Encrypt file content using Fernet symmetric encryption
    Args:
        file_content: Raw bytes of the file
        key: Encryption key in bytes
    Returns:
        Encrypted content in bytes
    """
    f = Fernet(key)
    return f.encrypt(file_content)

def decrypt_file(encrypted_content, key):
    """
    Decrypt file content using Fernet symmetric encryption
    Args:
        encrypted_content: Encrypted bytes of the file
        key: Encryption key in bytes
    Returns:
        Decrypted content in bytes
    """
    f = Fernet(key)
    return f.decrypt(encrypted_content)