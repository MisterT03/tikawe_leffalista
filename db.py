import sqlite3

def get_db_connection():
    conn = sqlite3.connect("database.db")  # Luo tai avaa tietokanta
    conn.row_factory = sqlite3.Row  # Tulokset sanakirjamaisina objekteina
    return conn
