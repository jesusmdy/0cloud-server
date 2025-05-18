from cryptography.fernet import Fernet

class FernetController:
  def generate_key():
    return Fernet.generate_key()
  
  def encrypt(key, data):
    f = Fernet(key)
    return f.encrypt(data)
  
  def decrypt(encrypted_data, key):
    f = Fernet(key)
    return f.decrypt(encrypted_data)