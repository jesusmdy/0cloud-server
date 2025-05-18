from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from controllers.fernet import FernetController
from cryptography.fernet import Fernet
from crypto.keys import generate_key_from_password

import base64
import os

class CryptoController:
  """
  Class for cryptographic operations.
  """
  
  class Misc:
    """
    Class for misc operations.
    """

    @staticmethod
    def gen_user_salt() -> bytes:
      """
      Generate a salt for a user.
      """
      return os.urandom(16)
    
    @staticmethod
    def gen_user_crypto(password: str) -> tuple:
      """
      Generate a user's crypto.
      """
      salt = CryptoController.Misc.gen_user_salt()
      
      user_key = CryptoController.Password.key_from_password(password, salt)
      
      private_key_bytes = CryptoController.Key.generate()
      
      encrypted_private_key = CryptoController.Key.encrypt(user_key, private_key_bytes)
      encrypted_private_key_with_salt = CryptoController.Base64.encode(salt + encrypted_private_key).decode('utf-8')
      
      encrypted_password = CryptoController.Password.encrypt(password, private_key_bytes)
      
      password_hash = CryptoController.Base64.encode(encrypted_password).decode('utf-8')
      
      return (encrypted_private_key_with_salt, password_hash)

  class Key:
    """
    Class for key operations.
    """

    @staticmethod
    def generate() -> bytes:
      """
      Generate a key for encryption/decryption.
      """
      return FernetController.generate_key()

    @staticmethod
    def encrypt(key: bytes, data: bytes) -> bytes:
      """
      Encrypt data with a key.
      
      Parameters:
      key (bytes): Key for encryption.
      data (bytes): Data to encrypt.
      
      Returns:
      bytes: Encrypted data.
      """
      return FernetController.encrypt(key, data)
    
    @staticmethod
    def decrypt(encrypted_data: bytes, key: bytes) -> bytes:
      """
      Decrypt data with a key.
      
      Parameters:
      encrypted_data (bytes): Encrypted data.
      key (bytes): Key for decryption.
      
      Returns:
      bytes: Decrypted data.
      """
      return FernetController.decrypt(encrypted_data, key)

  class Password:
    """
    Class for password operations.
    """

    @staticmethod
    def encrypt(password: str, key: bytes) -> bytes:
      """
      Encrypt a password with a key.
      
      Parameters:
      password (str): Password to encrypt.
      key (bytes): Key for encryption.
      
      Returns:
      bytes: Encrypted password.
      """
      return FernetController.encrypt(key, password.encode("utf-8"))

    @staticmethod
    def decrypt(encrypted_password: bytes, key: bytes) -> str:
      """
      Decrypt a password with a key.
      
      Parameters:
      encrypted_password (bytes): Encrypted password.
      key (bytes): Key for decryption.
      
      Returns:
      str: Decrypted password.
      """
      return FernetController.decrypt(encrypted_password, key).decode()
    
    @staticmethod
    def key_from_password(password: str, salt: bytes) -> bytes:
      """
      Generate a key from a password using PBKDF2.
      
      Parameters:
      password (str): Password to generate key from.
      salt (bytes): Salt for PBKDF2.
      
      Returns:
      bytes: Generated key.
      """
      return CryptoController.PBKDF2.generate_key(password, salt)

  class PBKDF2:
    """
    Class for PBKDF2 operations.
    """

    @staticmethod
    def generate_key(password: str, salt: bytes) -> bytes:
      """
      Generate a key from a password using PBKDF2.
      
      Parameters:
      password (str): Password to generate key from.
      salt (bytes): Salt for PBKDF2.
      
      Returns:
      bytes: Generated key.
      """
      kdf = PBKDF2HMAC(
          algorithm=hashes.SHA256(),
          length=32,
          salt=salt,
          iterations=100000,
      )
      return base64.urlsafe_b64encode(kdf.derive(password.encode()))

  class Base64:
    """
    Class for base64 operations.
    """

    @staticmethod
    def encode(data: bytes) -> bytes:
      """
      Encode data using base64.
      
      Parameters:
      data (bytes): Data to encode.
      
      Returns:
      bytes: Encoded data.
      """
      return base64.b64encode(data)

    @staticmethod
    def decode(data: bytes) -> bytes:
      """
      Decode data using base64.
      
      Parameters:
      data (bytes): Data to decode.
      
      Returns:
      bytes: Decoded data.
      """
      return base64.b64decode(data)

    @staticmethod
    def urlsafe_encode(data: bytes) -> bytes:
      """
      Encode data using urlsafe base64.
      
      Parameters:
      data (bytes): Data to encode.
      
      Returns:
      bytes: Encoded data.
      """
      return base64.urlsafe_b64encode(data)

    @staticmethod
    def urlsafe_decode(data: bytes) -> bytes:
      """
      Decode data using urlsafe base64.
      
      Parameters:
      data (bytes): Data to decode.
      
      Returns:
      bytes: Decoded data.
      """
      return base64.urlsafe_b64decode(data)