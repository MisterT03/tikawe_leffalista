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
            session['username'] = user['username']
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
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        search_query = request.form['search']
        cursor.execute("""
            SELECT movies.*, users.username FROM movies
            JOIN users ON users.id = movies.user_id
            WHERE title LIKE ? OR year LIKE ?
        """, (f"%{search_query}%", f"%{search_query}%"))
    else:
        cursor.execute("""
            SELECT movies.*, users.username FROM movies
            JOIN users ON users.id = movies.user_id
        """)

    movie_rows = cursor.fetchall()

    movies = []
    for movie in movie_rows:
        cursor.execute("""
            SELECT categories.name FROM categories
            JOIN movie_categories ON movie_categories.category_id = categories.id
            WHERE movie_categories.movie_id = ?
        """, (movie['id'],))
        categories = [row["name"] for row in cursor.fetchall()]

        movie_dict = dict(movie)
        movie_dict["categories"] = ', '.join(categories) if categories else "Ei määriteltyjä kategorioita"
        movies.append(movie_dict)

    conn.close()
    return render_template('movies.html', movies=movies, user_id=user_id)


@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        selected_categories = request.form.getlist('categories')

        cursor.execute("INSERT INTO movies (title, genre, year, user_id) VALUES (?, ?, ?, ?)",
                       (title, "", year, session['user_id']))
        movie_id = cursor.lastrowid

        for cat_id in selected_categories:
            cursor.execute("INSERT INTO movie_categories (movie_id, category_id) VALUES (?, ?)", (movie_id, cat_id))

        conn.commit()
        conn.close()
        flash('Elokuva lisätty onnistuneesti!')
        return redirect(url_for('movies'))

    conn.close()
    return render_template('add_movie.html', categories=categories)

@app.route('/delete_movie/<int:movie_id>')
def delete_movie(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()

    if movie is None or movie['user_id'] != session['user_id']:
        flash('Et voi poistaa muiden elokuvia!')
        return redirect(url_for('movies'))

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

    if movie is None or movie['user_id'] != session['user_id']:
        flash('Et voi muokata muiden elokuvia!')
        return redirect(url_for('movies'))

    cursor.execute("SELECT * FROM categories")
    categories = cursor.fetchall()

    cursor.execute("""
        SELECT category_id FROM movie_categories WHERE movie_id = ?
    """, (movie_id,))
    selected_category_ids = [row['category_id'] for row in cursor.fetchall()]

    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        selected_categories = request.form.getlist('categories')

        cursor.execute("""
            UPDATE movies SET title = ?, year = ? WHERE id = ?
        """, (title, year, movie_id))

        cursor.execute("DELETE FROM movie_categories WHERE movie_id = ?", (movie_id,))

        for cat_id in selected_categories:
            cursor.execute("""
                INSERT INTO movie_categories (movie_id, category_id) VALUES (?, ?)
            """, (movie_id, cat_id))

        conn.commit()
        conn.close()
        flash('Elokuva päivitetty onnistuneesti!')
        return redirect(url_for('movies'))

    conn.close()
    return render_template('edit_movie.html', movie=movie, categories=categories, selected_category_ids=selected_category_ids)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Olet kirjautunut ulos')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    user_id = session['user_id']

    cursor.execute("SELECT COUNT(*) FROM movies WHERE user_id = ?", (user_id,))
    movie_count = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(year) FROM movies WHERE user_id = ?", (user_id,))
    avg_year = cursor.fetchone()[0]

    cursor.execute("""
        SELECT category_id, COUNT(*) AS count
        FROM movie_categories
        JOIN categories ON movie_categories.category_id = categories.id
        WHERE movie_categories.movie_id IN (SELECT id FROM movies WHERE user_id = ?)
        GROUP BY category_id
        ORDER BY count DESC
        LIMIT 1
    """, (user_id,))
    most_common_genre = cursor.fetchone()
    most_common_genre = most_common_genre['category_id'] if most_common_genre else None

    if most_common_genre:
        cursor.execute("SELECT name FROM categories WHERE id = ?", (most_common_genre,))
        most_common_genre = cursor.fetchone()['name']
    else:
        most_common_genre = "Ei genrejä"

    cursor.execute("""
        SELECT movies.title, movies.year, categories.name
        FROM movies
        LEFT JOIN movie_categories ON movie_categories.movie_id = movies.id
        LEFT JOIN categories ON categories.id = movie_categories.category_id
        WHERE movies.user_id = ?
    """, (user_id,))
    user_movies = cursor.fetchall()

    user_movies_combined = []
    for movie in user_movies:
        found_movie = next((item for item in user_movies_combined if item['title'] == movie['title']), None)
        if found_movie:
            found_movie['genres'].append(movie['name'])
        else:
            user_movies_combined.append({'title': movie['title'], 'year': movie['year'], 'genres': [movie['name']]})

    conn.close()

    return render_template('profile.html',
                           movie_count=movie_count,
                           avg_year=avg_year,
                           most_common_genre=most_common_genre,
                           user_movies=user_movies_combined)

@app.route('/add_comment/<int:movie_id>', methods=['POST'])
def add_comment(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    content = request.form['content']
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("INSERT INTO comments (movie_id, user_id, content) VALUES (?, ?, ?)",
                   (movie_id, user_id, content))

    conn.commit()
    conn.close()

    flash('Kommentti lisätty onnistuneesti!')
    return redirect(url_for('movie_details', movie_id=movie_id))

@app.route('/movie/<int:movie_id>', methods=['GET', 'POST'])
def movie_details(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()

    cursor.execute("""
        SELECT categories.name FROM categories
        JOIN movie_categories ON movie_categories.category_id = categories.id
        WHERE movie_categories.movie_id = ?
    """, (movie_id,))
    categories = [row['name'] for row in cursor.fetchall()]

    cursor.execute("""
        SELECT comments.comment, users.username 
        FROM comments 
        JOIN users ON users.id = comments.user_id 
        WHERE comments.movie_id = ?
    """, (movie_id,))
    comments = cursor.fetchall()

    if request.method == 'POST':
        comment = request.form['comment']
        user_id = session['user_id']
        cursor.execute("INSERT INTO comments (movie_id, user_id, comment) VALUES (?, ?, ?)", 
                       (movie_id, user_id, comment))
        conn.commit()
        flash("Kommentti lisätty onnistuneesti!")
        return redirect(url_for('movie_details', movie_id=movie_id))

    conn.close()

    return render_template('movie_details.html', movie=movie, categories=categories, comments=comments)

if __name__ == '__main__':
    app.run(debug=True)
