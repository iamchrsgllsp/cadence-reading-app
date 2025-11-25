## Set up quick sqlite connection then migrate to supbase

import sqlite3
from sqlite3 import Connection
import json

def get_db_connection() -> Connection:
    conn = sqlite3.connect('database.db')
    return conn

def initialize_database():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topfive (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            items TEXT NOT NULL DEFAULT '[]'  -- JSON-encoded list
        )
    ''')
    conn.commit()
    conn.close()

def initialize_library():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            book TEXT NOT NULL DEFAULT '[]',  -- JSON-encoded list,
            status TEXT,
            pages_read INTEGER,
            total_pages INTEGER,
            version TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_top_five_by_username(username: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM topfive WHERE username = ?', (username,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_library(user):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM library where username = ?', (user,))
    row = cursor.fetchall()
    conn.close()
    return row

def amend_top_five(username: str, items: list):
    conn = get_db_connection()
    cursor = conn.cursor()
    items_json = json.dumps(items)
    cursor.execute('''
        INSERT INTO topfive (username, items)
        VALUES (?, ?)
    ''', (username, items_json))
    conn.commit()
    conn.close()



#update this to include all book items - current status, pages read, tbr or completed etc
#also add check to see if book already exists for user
def add_book_to_library(user: str,book: list,pages: int):
    print(user)
    initialize_library()
    conn = get_db_connection()
    cursor = conn.cursor()
    items_json = json.dumps(book)
    cursor.execute('''
        INSERT INTO library (username, book, total_pages)
        VALUES (?, ?, ?)
    ''', (user, items_json,pages))
    conn.commit()
    conn.close()

def remove_from_library(user: str,book: int):
    print(user)
    print(book)
    initialize_library()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM library WHERE username = ? AND id = ?
    ''', (user, book))
    conn.commit()
    conn.close()

def update_book_progress(user: str, book_id: int, pages_read: int):
    initialize_library()
    print(pages_read)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE library
        SET pages_read = ?
        WHERE username = ? AND id = ?
    ''', (pages_read, user, book_id))
    conn.commit()
    conn.close()

def update_currentbook(user: str, book_id: int):
    initialize_library()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE library
        SET status = ?
        WHERE username = ? AND id = ?
    ''', ('reading', user, book_id))
    conn.commit()
    conn.close()