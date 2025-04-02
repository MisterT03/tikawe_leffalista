import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from db import create_tables

create_tables()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']

        if password1 != password2:
            flash('Salasanat eivät täsmää!')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password1)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Käyttäjänimi on jo käytössä')
            return redirect(url_for('register'))
        finally:
            conn.close()

        flash('Käyttäjä luotu onnistuneesti!')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            flash('Tervetuloa takaisin!')
            return redirect(url_for('movies'))
        else:
            flash('Virheellinen tunnus tai salasana')
    return render_template('login.html')

@app.route('/movies', methods=['GET', 'POST'])
def movies():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    if request.method == 'POST':
        search_query = request.form['search']
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM movies
            WHERE user_id = ? AND (title LIKE ? OR genre LIKE ? OR year LIKE ?)
        """, (user_id, f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))

        movies = cursor.fetchall()

        conn.close()
    else:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM movies WHERE user_id = ?", (user_id,))
        movies = cursor.fetchall()

        conn.close()

    return render_template('movies.html', movies=movies)

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        year = request.form['year']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO movies (title, genre, year, user_id) VALUES (?, ?, ?, ?)", (title, genre, year, session['user_id']))
        conn.commit()
        conn.close()
        flash('Elokuva lisätty onnistuneesti!')
        return redirect(url_for('movies'))
    return render_template('add_movie.html')

@app.route('/delete_movie/<int:movie_id>')
def delete_movie(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()
    flash('Elokuva poistettu onnistuneesti!')
    return redirect(url_for('movies'))

@app.route('/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()

    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        year = request.form['year']
        cursor.execute("UPDATE movies SET title = ?, genre = ?, year = ? WHERE id = ?", (title, genre, year, movie_id))
        conn.commit()
        conn.close()
        flash('Elokuva päivitetty onnistuneesti!')
        return redirect(url_for('movies'))
    conn.close()
    return render_template('edit_movie.html', movie=movie)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Olet kirjautunut ulos')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
