from cryptography.fernet import Fernet
from PIL import Image
import io
import os
from storage.files import ENCRYPTED_FILES_DIR
import uuid
from storage.files import get_encrypted_file
import json
import base64

def encrypt_file_content(
  file_content: bytes,
  private_key: str
):
  f = Fernet(private_key.encode())
  encrypted_content = f.encrypt(file_content)
  return encrypted_content

def decrypt_file_content(
  encrypted_content: bytes,
  private_key: str
):
    try:
        f = Fernet(private_key.encode())
        decrypted_content = f.decrypt(encrypted_content)
    except Exception as e:
        return None
    return decrypted_content


def generate_encrypted_thumbnails(
  file_content: bytes,
  private_key: str,
):
  thumbnails = {}
  for size in [(128, 128), (256, 256), (512, 512)]:
    file_id = uuid.uuid4()
    
    img = Image.open(io.BytesIO(file_content))
    img.thumbnail(size)
    buffer = io.BytesIO()
    
    img.save(buffer, format='PNG')
    mime_type = 'image/png'
    
    file_size = len(buffer.getvalue())
    file_content = buffer.getvalue()
    
    encrypted_content = encrypt_file_content(file_content, private_key)
    encrypted_filename = f"{str(file_id)}.enc"

    size_key = f"{size[0]}x{size[1]}"

    thumbnails[size_key] = {
      "file_id": str(file_id),
      "encrypted_filename": encrypted_filename,
      "file_size": file_size,
      "mime_type": mime_type
    }
    with open(os.path.join(ENCRYPTED_FILES_DIR, encrypted_filename), 'wb') as f:
      f.write(encrypted_content)
    
  return thumbnails

def encrypted_to_base64(
  encrypted_content: bytes,
  mime_type: str
):
  return "data:" + mime_type + ";base64," + base64.b64encode(encrypted_content).decode('utf-8')

def decrypt_thumbnails_list(
  thumbnails: list,
  private_key: str
):
  decrypted_thumbnails = []
  for thumbnail in thumbnails:
    encrypted_content = get_encrypted_file(thumbnail['file_id'])
    if not encrypted_content:
      return None

    decrypted_content = decrypt_file_content(encrypted_content, private_key)
    decrypted_thumbnails.append({
      "file_id": thumbnail['file_id'],
      "file_size": thumbnail['file_size'],
      "mime_type": thumbnail['mime_type'],
      "file_content": encrypted_to_base64(decrypted_content, thumbnail['mime_type']) if decrypted_content else None
    })
  return decrypted_thumbnails
  