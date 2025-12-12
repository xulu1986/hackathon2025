import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

class ChatRepository:
    """
    Handles data persistence using SQLite.
    Manages chat sessions and messages.
    """
    
    def __init__(self, db_path: str = "chat_history.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        """Creates a database connection with row factory."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initializes the database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()

    def create_session(self, title: str = "New Chat") -> int:
        """Creates a new chat session and returns its ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO sessions (title) VALUES (?)', (title,))
        session_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return session_id

    def get_all_sessions(self) -> List[Dict]:
        """Retrieves all chat sessions ordered by newest first."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM sessions ORDER BY created_at DESC')
        sessions = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return sessions

    def get_messages(self, session_id: int) -> List[Dict]:
        """Retrieves all messages for a specific session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM messages WHERE session_id = ? ORDER BY id ASC', (session_id,))
        messages = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        return messages

    def add_message(self, session_id: int, role: str, content: str):
        """Adds a message to a session."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)',
            (session_id, role, content)
        )
        
        # Optionally update session title if it's the first user message
        if role == "user":
            # Check if it's the first message (or just update title based on first user msg)
            cursor.execute('SELECT count(*) as count FROM messages WHERE session_id = ?', (session_id,))
            count = cursor.fetchone()['count']
            if count <= 2: # 1 msg just added, so count is 1. Or request + response.
                # Update title to first ~30 chars of prompt
                new_title = content[:30] + "..." if len(content) > 30 else content
                cursor.execute('UPDATE sessions SET title = ? WHERE id = ?', (new_title, session_id))

        conn.commit()
        conn.close()

    def delete_session(self, session_id: int):
        """Deletes a session and its messages."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
        conn.commit()
        conn.close()

