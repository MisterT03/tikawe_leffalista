import sqlite3
import secrets
from flask import Flask, render_template, request, redirect, url_for, flash, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from db import create_tables

create_tables()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'

def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
        abort(403)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    if request.method == 'POST':
        check_csrf()
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']

        if not username or not password1 or not password2:
            flash('Käyttäjätunnus ja salasana eivät voi olla tyhjiä!', 'error')
            return redirect(url_for('register'))

        if password1 != password2:
            flash('Salasanat eivät täsmää!', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password1)
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            flash('Käyttäjänimi on jo käytössä', 'error')
            return redirect(url_for('register'))
        finally:
            conn.close()

        flash('Käyttäjä luotu onnistuneesti!')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
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
            session['csrf_token'] = secrets.token_hex(16)
            flash('Tervetuloa takaisin!')
            return redirect(url_for('movies'))
        else:
            flash('Virheellinen tunnus tai salasana')
    return render_template('login.html')


@app.route('/movies', methods=['GET', 'POST'])
def movies():
    if 'user_id' not in session:
        flash("Sinun täytyy olla kirjautunut nähdäksesi elokuvat.", "error")
        return redirect(url_for('login'))
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        check_csrf()
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

@app.route("/add", methods=["GET", "POST"])
def add_movie():
    if "user_id" not in session:
        flash("Kirjaudu sisään lisätäksesi elokuvia.")
        return redirect("/login")

    conn = get_db_connection()
    categories = conn.execute("SELECT * FROM categories").fetchall()

    if request.method == "POST":
        check_csrf()
        title = request.form["title"].strip()
        try:
            year = int(request.form["year"])
        except ValueError:
            flash("Vuosi pitää olla numero.", "error")
            conn.close()
            return redirect(request.url)

        new_category = request.form.get("new_category", "").strip()
        selected_ids = request.form.getlist("categories")

        if len(title) > 100:
            flash("Elokuvan nimi on liian pitkä.")
            conn.close()
            return redirect(request.url)

        if new_category:
            existing = conn.execute("SELECT id FROM categories WHERE name = ?", (new_category,)).fetchone()
            if existing:
                new_id = existing["id"]
            else:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (new_category,))
                new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            selected_ids.append(str(new_id))

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO movies (title, genre, year, user_id) VALUES (?, ?, ?, ?)",
            (title, new_category or "Määrittelemätön", year, session["user_id"])
        )
        movie_id = cursor.lastrowid

        for cid in selected_ids:
            conn.execute("INSERT INTO movie_categories (movie_id, category_id) VALUES (?, ?)", (movie_id, int(cid)))

        conn.commit()
        conn.close()
        flash("Elokuva lisätty onnistuneesti!")
        return redirect("/movies")

    conn.close()
    return render_template("add_movie.html", categories=categories)

@app.route('/delete_movie/<int:movie_id>', methods=['POST'])
def delete_movie(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    check_csrf()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()

    if movie is None or movie['user_id'] != session['user_id']:
        flash('Et voi poistaa muiden elokuvia!')
        conn.close()
        return redirect(url_for('movies'))

    cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()
    flash('Elokuva poistettu onnistuneesti!')
    return redirect(url_for('movies'))

@app.route("/edit/<int:movie_id>", methods=["GET", "POST"])
def edit_movie(movie_id):
    if "user_id" not in session:
        flash("Kirjaudu sisään muokataksesi elokuvia.")
        return redirect("/login")

    conn = get_db_connection()
    movie = conn.execute("SELECT * FROM movies WHERE id = ? AND user_id = ?", (movie_id, session["user_id"])).fetchone()
    if not movie:
        conn.close()
        flash("Elokuvaa ei löydy tai ei oikeuksia.")
        return redirect("/movies")

    categories = conn.execute("SELECT * FROM categories").fetchall()

    if request.method == "POST":
        check_csrf()

        title = request.form["title"].strip()
        try:
            year = int(request.form["year"])
        except ValueError:
            flash("Vuosi pitää olla numero.", "error")
            return redirect(request.url)

        new_category = request.form.get("new_category", "").strip()
        selected_ids = request.form.getlist("categories")

        if len(title) > 150:
            flash("Elokuvan nimi on liian pitkä. Maximi on 150 merkkiä.")
            return redirect(request.url)

        conn.execute("UPDATE movies SET title = ?, year = ? WHERE id = ?", (title, year, movie_id))

        if new_category:
            existing = conn.execute("SELECT id FROM categories WHERE name = ?", (new_category,)).fetchone()
            if existing:
                new_id = existing["id"]
            else:
                conn.execute("INSERT INTO categories (name) VALUES (?)", (new_category,))
                new_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            selected_ids.append(str(new_id))

        conn.execute("DELETE FROM movie_categories WHERE movie_id = ?", (movie_id,))
        for cid in selected_ids:
            conn.execute("INSERT INTO movie_categories (movie_id, category_id) VALUES (?, ?)", (movie_id, int(cid)))

        conn.commit()
        conn.close()
        flash("Elokuva päivitetty onnistuneesti!")
        return redirect("/movies")

    selected_rows = conn.execute("SELECT category_id FROM movie_categories WHERE movie_id = ?", (movie_id,)).fetchall()
    selected_category_ids = [row["category_id"] for row in selected_rows]
    conn.close()

    return render_template("edit_movie.html", movie=movie, categories=categories, selected_category_ids=selected_category_ids)


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
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

@app.route('/movie/<int:movie_id>', methods=['GET', 'POST'])
def movie_details(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
    movie = cursor.fetchone()

    if movie is None:
        flash("Elokuvaa ei löytynyt.", "error")
        conn.close()
        return redirect(url_for('index'))

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

    user_rating = None
    if 'user_id' in session:
        cursor.execute("""
            SELECT rating FROM ratings WHERE movie_id = ? AND user_id = ?
        """, (movie_id, session['user_id']))
        user_rating_row = cursor.fetchone()
        if user_rating_row:
            user_rating = user_rating_row['rating']

    cursor.execute("""
        SELECT AVG(rating) as avg_rating FROM ratings WHERE movie_id = ?
    """, (movie_id,))
    avg_rating_row = cursor.fetchone()
    avg_rating = avg_rating_row['avg_rating'] if avg_rating_row['avg_rating'] else None

    if request.method == 'POST':
        check_csrf()
        if 'comment' in request.form:
            comment = request.form['comment'].strip()

            if len(comment) > 500:
                flash("Kommentin maksimipituus on 500 merkkiä.", "error")
                conn.close()
                return redirect(url_for('movie_details', movie_id=movie_id))

            user_id = session['user_id']
            try:
                cursor.execute("INSERT INTO comments (movie_id, user_id, comment) VALUES (?, ?, ?)",
                               (movie_id, user_id, comment))
                conn.commit()
                flash("Kommentti lisätty onnistuneesti!")
            except Exception as e:
                flash(f"Virhe kommentin lisäämisessä: {e}", "error")
            conn.close()
            return redirect(url_for('movie_details', movie_id=movie_id))

        elif 'rating' in request.form:
            rating = request.form['rating']
            try:
                rating = int(rating)
                if not (1 <= rating <= 5):
                    raise ValueError("Virheellinen arvosana")

                user_id = session['user_id']
                cursor.execute("""
                    INSERT INTO ratings (movie_id, user_id, rating)
                    VALUES (?, ?, ?)
                    ON CONFLICT(movie_id, user_id)
                    DO UPDATE SET rating=excluded.rating
                """, (movie_id, user_id, rating))
                conn.commit()
                flash("Arvosana tallennettu onnistuneesti.")
            except Exception as e:
                flash(f"Virhe arvosanan tallentamisessa: {e}", "error")
            conn.close()
            return redirect(url_for('movie_details', movie_id=movie_id))

    conn.close()

    return render_template('movie_details.html', movie=movie, categories=categories, comments=comments, 
                           user_rating=user_rating, avg_rating=avg_rating)

@app.route('/movies/<int:movie_id>/rate', methods=['POST'])
def rate_movie(movie_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    check_csrf()

    rating = request.form.get('rating')
    user_id = session['user_id']

    try:
        rating = int(rating)
        if not (1 <= rating <= 5):
            raise ValueError("Virheellinen arvosana")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO ratings (movie_id, user_id, rating)
            VALUES (?, ?, ?)
            ON CONFLICT(movie_id, user_id)
            DO UPDATE SET rating=excluded.rating
        """, (movie_id, user_id, rating))

        conn.commit()
        conn.close()

        flash("Arvosana tallennettu onnistuneesti.")
    except Exception as e:
        flash(f"Virhe: {e}")

    return redirect(url_for('movie_details', movie_id=movie_id))

if __name__ == '__main__':
    app.run(debug=True)
