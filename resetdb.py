import sqlite3

DATABASE = "database.db"

def clear_database():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS users")
    cursor.execute("DROP TABLE IF EXISTS movies")
    cursor.execute("DROP TABLE IF EXISTS categories")
    cursor.execute("DROP TABLE IF EXISTS movie_categories")

    conn.commit()
    conn.close()

    print("Tietokanta on tyhjennetty!")

if __name__ == "__main__":
    clear_database()
