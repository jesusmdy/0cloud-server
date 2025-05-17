import sqlite3
import os
from datetime import datetime
import uuid

DB_PATH = 'files.db'
ENCRYPTED_FILES_DIR = 'encrypted_files'

# Ensure encrypted files directory exists
os.makedirs(ENCRYPTED_FILES_DIR, exist_ok=True)

def init_db():
    """Initialize the database with required tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            encrypted_private_key TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL
        )
    ''')
    
    # Create folders table
    c.execute('''
        CREATE TABLE IF NOT EXISTS folders (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            parent_id TEXT,
            created_at TIMESTAMP NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (parent_id) REFERENCES folders (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create files table (removed encrypted_content column)
    c.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            encrypted_filename TEXT UNIQUE NOT NULL,
            original_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            parent_id TEXT,
            created_at TIMESTAMP NOT NULL,
            mime_type TEXT NOT NULL,
            user_id TEXT NOT NULL,
            FOREIGN KEY (parent_id) REFERENCES folders (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def save_encrypted_file(file_id: str, encrypted_content: bytes) -> str:
    """Save encrypted file to disk and return the file path."""
    file_path = os.path.join(ENCRYPTED_FILES_DIR, f"{file_id}.enc")
    with open(file_path, 'wb') as f:
        f.write(encrypted_content)
    return file_path

def get_encrypted_file(file_id: str) -> bytes:
    """Read encrypted file from disk."""
    file_path = os.path.join(ENCRYPTED_FILES_DIR, f"{file_id}.enc")
    with open(file_path, 'rb') as f:
        return f.read()

def delete_encrypted_file(file_id: str):
    """Delete encrypted file from disk."""
    file_path = os.path.join(ENCRYPTED_FILES_DIR, f"{file_id}.enc")
    if os.path.exists(file_path):
        os.remove(file_path)

def save_file(encrypted_filename: str, original_filename: str, encrypted_content: bytes, file_size: int, user_id: str, parent_id: str = None, mime_type: str = 'application/octet-stream') -> dict:
    """Save a file to the database and encrypted content to disk."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Generate a UUID for the file
    file_id = str(uuid.uuid4())
    
    # Get current timestamp
    created_at = datetime.now()
    
    # Save encrypted content to disk
    save_encrypted_file(file_id, encrypted_content)
    
    # Insert the file into the database
    c.execute('''
        INSERT INTO files (id, encrypted_filename, original_filename, file_size, parent_id, mime_type, user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (file_id, encrypted_filename, original_filename, file_size, parent_id, mime_type, user_id, created_at))
    
    conn.commit()
    
    # Get the created file data
    c.execute('''
        SELECT id, encrypted_filename, original_filename, file_size, parent_id, created_at, mime_type, user_id
        FROM files
        WHERE id = ?
    ''', (file_id,))
    
    row = c.fetchone()
    conn.close()
    
    return {
        'id': row[0],
        'encrypted_filename': row[1],
        'original_filename': row[2],
        'file_size': row[3],
        'parent_id': row[4],
        'created_at': row[5],
        'mime_type': row[6],
        'user_id': row[7]
    }

def get_file(encrypted_filename):
    """Get file from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT id, encrypted_filename, original_filename, encrypted_content, file_size, mime_type, parent_id, created_at, user_id
            FROM files
            WHERE encrypted_filename = ?
        ''', (encrypted_filename,))
        
        row = c.fetchone()
        if row:
            return {
                'id': row[0],
                'encrypted_filename': row[1],
                'original_filename': row[2],
                'encrypted_content': row[3],
                'file_size': row[4],
                'mime_type': row[5],
                'parent_id': row[6],
                'created_at': row[7],
                'user_id': row[8]
            }
        return None
    finally:
        conn.close()

def get_file_by_id(file_id):
    """Get file from database by its ID and read encrypted content from disk."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT id, encrypted_filename, original_filename, file_size, mime_type, parent_id, created_at, user_id
            FROM files
            WHERE id = ?
        ''', (file_id,))
        
        row = c.fetchone()
        if row:
            # Read encrypted content from disk
            encrypted_content = get_encrypted_file(file_id)
            
            return {
                'id': row[0],
                'encrypted_filename': row[1],
                'original_filename': row[2],
                'encrypted_content': encrypted_content,
                'file_size': row[3],
                'mime_type': row[4],
                'parent_id': row[5],
                'created_at': row[6],
                'user_id': row[7]
            }
        return None
    finally:
        conn.close()

def delete_file(file_id):
    """Delete file from database and encrypted content from disk."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Delete file from database
        c.execute('DELETE FROM files WHERE id = ?', (file_id,))
        conn.commit()
        
        # Delete encrypted file from disk
        delete_encrypted_file(file_id)
    finally:
        conn.close()

def count_user_filesize(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT SUM(file_size) FROM files WHERE user_id = ?
        ''', (user_id,))
        
        result = c.fetchone()
        return result[0] if result[0] else 0
    finally:
        conn.close()

def list_files(search_term='', limit=None, offset=None, parent_id=None, user_id=None):
    """List all files with optional search, pagination and parent folder filtering"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        # Build the query
        query = '''
            SELECT f.id, f.encrypted_filename, f.original_filename, f.created_at, 
                   f.parent_id, f.file_size, f.mime_type, f.user_id
            FROM files f
            WHERE 1=1
        '''
        params = []
        
        if search_term:
            query += ' AND f.original_filename LIKE ?'
            params.append(f'%{search_term}%')
            
        if parent_id is not None:
            query += ' AND f.parent_id = ?'
            params.append(parent_id)
            
        if user_id is not None:
            query += ' AND f.user_id = ?'
            params.append(user_id)
            
        # Get total count
        count_query = f"SELECT COUNT(*) FROM ({query})"
        c.execute(count_query, params)
        total = c.fetchone()[0]
        
        # Add ordering and pagination
        query += ' ORDER BY f.created_at DESC'
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
        if offset is not None:
            query += ' OFFSET ?'
            params.append(offset)
            
        # Execute final query
        c.execute(query, params)
        rows = c.fetchall()
        
        return [{
                'id': row[0],
                'encrypted_filename': row[1],
                'original_filename': row[2],
                'created_at': row[3],
                'parent_id': row[4],
                'file_size': row[5],
                'mime_type': row[6],
                'user_id': row[7]
            } for row in rows]
    finally:
        conn.close()

def create_folder(name: str, user_id: str, parent_id: str = None) -> dict:
    """Create a new folder."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Generate a UUID for the folder
    folder_id = str(uuid.uuid4())
    
    # Get current timestamp
    created_at = datetime.utcnow().isoformat()
    
    # Insert the folder into the database
    c.execute('''
        INSERT INTO folders (id, name, parent_id, created_at, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (folder_id, name, parent_id, created_at, user_id))
    
    conn.commit()
    
    # Get the created folder data
    c.execute('''
        SELECT id, name, parent_id, created_at, user_id
        FROM folders
        WHERE id = ?
    ''', (folder_id,))
    
    row = c.fetchone()
    conn.close()
    
    return {
        'id': row[0],
        'name': row[1],
        'parent_id': row[2],
        'created_at': row[3],
        'user_id': row[4]
    }

def get_folder(folder_id):
    """Get folder details"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT id, name, parent_id, created_at, user_id
            FROM folders
            WHERE id = ?
        ''', (folder_id,))
        
        row = c.fetchone()
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'parent_id': row[2],
                'created_at': row[3],
                'user_id': row[4]
            }
        return None
    finally:
        conn.close()

def list_folders(parent_id=None, user_id=None):
    """List all folders with optional parent filtering"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        query = '''
            SELECT id, name, parent_id, created_at, user_id
            FROM folders
            WHERE 1=1
        '''
        params = []
        
        if parent_id is not None:
            query += ' AND parent_id = ?'
            params.append(parent_id)
            
        if user_id is not None:
            query += ' AND user_id = ?'
            params.append(user_id)
            
        query += ' ORDER BY name ASC'
        
        c.execute(query, params)
        rows = c.fetchall()
        
        return [{
            'id': row[0],
            'name': row[1],
            'parent_id': row[2],
            'created_at': row[3],
            'user_id': row[4]
        } for row in rows]
    finally:
        conn.close()

def list_all_files():
    """List all files with their user_ids for debugging."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('''
            SELECT id, encrypted_filename, original_filename, user_id
            FROM files
            ORDER BY created_at DESC
        ''')
        
        rows = c.fetchall()
        return [{
            'id': row[0],
            'encrypted_filename': row[1],
            'original_filename': row[2],
            'user_id': row[3]
        } for row in rows]
    finally:
        conn.close()

def user_exists(user_id):
    """Check if a user exists by ID."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        c.execute('SELECT 1 FROM users WHERE id = ?', (user_id,))
        return c.fetchone() is not None
    finally:
        conn.close() 