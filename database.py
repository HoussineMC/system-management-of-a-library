import os
import re
import bcrypt
import sqlite3
import logging
from dotenv import load_dotenv


current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, 'manager.env'))

ADMIN_USER    = os.getenv('ADMIN_USER')
ADMIN_PASS    = os.getenv('ADMIN_PASS')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'library.db')
PEPPER        = os.getenv('PEPPER', 'default-pepper').encode()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('library.log'), logging.StreamHandler()]
)

def create_database():
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                status TEXT DEFAULT 'Available',
                borrower_id INTEGER,
                book_type TEXT DEFAULT 'fiction',
                genre_or_subject TEXT,
                FOREIGN KEY (borrower_id) REFERENCES users (user_id)
            )
        ''')
        conn.commit()

def sign_up(username: str, password: str, email: str) -> bool:
    """Register a new user"""
    if not username or not password or not email:
        return False

    
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        logging.warning("Invalid email format")
        return False

    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT 1 FROM users WHERE username = ?', (username,))
            if cursor.fetchone():
                logging.warning("Username already exists")
                return False
            
            
            hashed = bcrypt.hashpw(password.encode() + PEPPER, bcrypt.gensalt())
            
            
            cursor.execute(
                'INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                (username, hashed, email)
            )
            conn.commit()
            logging.info(f"User {username} registered successfully")
            return True
            
    except sqlite3.Error as e:
        logging.error(f"Database error during sign up: {e}")
        return False

def login(username: str, password: str) -> dict:
    """Authenticate user and return user data if successful"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username, password, email FROM users WHERE username = ?', 
                         (username,))
            user = cursor.fetchone()
            
            if user and verify_password(password, user[2]): 
                return {
                    'user_id': user[0],
                    'username': user[1],
                    'email': user[3]
                }
            return None
    except sqlite3.Error as e:
        logging.error(f"Login error: {e}")
        return None

def get_all_users():
    with sqlite3.connect(DATABASE_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users")
        return [dict(row) for row in cursor.fetchall()]

def delete_user(user_id):
    with sqlite3.connect(DATABASE_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        logging.info(f"User {user_id} deleted.")

def add_book(title: str, author: str, book_type: str = 'fiction', genre_or_subject: str = None) -> bool:
    """Add a new book to the database"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            
            
            print(f"Adding book: {title=}, {author=}, {book_type=}, {genre_or_subject=}")
            
            cursor.execute('''
                INSERT INTO books (title, author, status, book_type, genre_or_subject)
                VALUES (?, ?, 'Available', ?, ?)
            ''', (title, author, book_type, genre_or_subject))
            
            conn.commit()
            logging.info(f"Book '{title}' by {author} added successfully")
            return True
            
    except sqlite3.Error as e:
        logging.error(f"Error adding book: {e}")
        print(f"Database error: {e}")  
        return False
    except Exception as e:
        logging.error(f"Unexpected error adding book: {e}")
        print(f"Unexpected error: {e}") 
        return False

def get_books():
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.book_id, b.title, b.author, b.status,
                       CASE WHEN u.username IS NOT NULL 
                            THEN u.username 
                            ELSE '-' 
                       END as borrower
                FROM books b
                LEFT JOIN users u ON b.borrower_id = u.user_id
                ORDER BY b.book_id
            ''')
            return cursor.fetchall()
    except sqlite3.Error as e:
        print(f"Error getting books: {e}")  
        return []

def get_books_by_author(author: str):
    """Get all books by a specific author"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.book_id, b.title, b.author, b.status, b.book_type, 
                       b.genre_or_subject, u.username
                FROM books b
                LEFT JOIN users u ON b.borrower_id = u.user_id 
                WHERE b.author LIKE ?
            ''', (f'%{author}%',))
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Error getting books by author: {e}")
        return []

def borrow_book(user, book_id):
    """Borrow a book"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            
            
            cursor.execute('SELECT status FROM books WHERE book_id = ?', (book_id,))
            result = cursor.fetchone()
            
            if not result:
                logging.error("Book not found")
                return False
                
            if result[0] != 'Available':
                logging.error("Book is not available")
                return False
                
           
            cursor.execute('''
                UPDATE books 
                SET status = 'Borrowed',
                    borrower_id = ?
                WHERE book_id = ?
            ''', (user['user_id'], book_id))
            conn.commit()
            logging.info(f"Book {book_id} borrowed by user {user['username']}")
            return True
            
    except sqlite3.Error as e:
        logging.error(f"Error borrowing book: {e}")
        return False

def return_book(user_id, book_id):
    """Return a book to the library"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            
            
            cursor.execute('''
                SELECT status, borrower_id 
                FROM books 
                WHERE book_id = ?
            ''', (book_id,))
            
            book = cursor.fetchone()
            
            if not book:
                print(f"Book {book_id} not found")  
                return False
                
            status, current_borrower = book
            
            if status != 'Borrowed' or current_borrower != user_id:
                print(f"Book status: {status}, borrower: {current_borrower}, user: {user_id}")  
                return False
            
            
            cursor.execute('''
                UPDATE books 
                SET status = 'Available',
                    borrower_id = NULL 
                WHERE book_id = ? 
            ''', (book_id,))
            
            conn.commit()
            return True
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")  
        return False

def get_book_types():
    return ['general', 'fiction', 'science']

def export_books_to_file(format='txt'):
    """Export books to a file"""
    try:
        books = get_books()
        if format == 'txt':
            with open('books_export.txt', 'w', encoding='utf-8') as f:
                for book in books:
                    f.write(f"ID: {book[0]}\n")
                    f.write(f"Title: {book[1]}\n")
                    f.write(f"Author: {book[2]}\n")
                    f.write(f"Status: {book[3]}\n")
                    f.write(f"Type: {book[4]}\n")
                    f.write(f"Genre/Subject: {book[5]}\n")
                    f.write("-" * 50 + "\n")
        return True
    except Exception as e:
        logging.error(f"Error exporting books: {e}")
        return False

def book_exists(title, author):
    """Check if book already exists"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM books WHERE title = ? AND author = ?', (title, author))
            return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logging.error(f"Book check error: {e}")
        return False



def get_all_users():
    """Get all registered users"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT user_id, username, email FROM users')
            return cursor.fetchall()
    except sqlite3.Error as e:
        logging.error(f"Error fetching users: {e}")
        return []

def delete_user(user_id):
    """Delete a user by ID"""
    try:
        with sqlite3.connect(DATABASE_NAME) as conn:
            cursor = conn.cursor()
            
            cursor.execute('UPDATE books SET borrower_id = NULL WHERE borrower_id = ?', (user_id,))
            
            cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
            conn.commit()
            return True
    except Exception as e:
        logging.error(f"Error deleting user: {str(e)}")
        return False



def hash_password(password: str) -> bytes:
    """Hash the password using bcrypt and pepper."""
    return bcrypt.hashpw(password.encode() + PEPPER, bcrypt.gensalt())

def verify_password(password: str, hashed: bytes) -> bool:
    """Verify the password against the hashed password."""
    return bcrypt.checkpw(password.encode() + PEPPER, hashed)



def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def validate_password(password: str) -> bool:
    """Validate password strength."""
    return len(password) >= 8 and any(c.isupper() for c in password)

if __name__ == "__main__":
    create_database()
