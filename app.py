from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secretkey'  # Vaihda tämä turvalliseksi salaiseksi avaimiksi
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Tietokannan sijainti
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Ei turhia muutosehälytyksiä
db = SQLAlchemy(app)

# Käyttäjätaulu
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('movies', lazy=True))

# Pääsivu
@app.route('/')
def index():
    return render_template('index.html')

# Rekisteröitymissivu
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']
        
        # Tarkistetaan, että salasanat täsmäävät
        if password1 != password2:
            flash('Salasanat eivät täsmää!')
            return redirect(url_for('register'))  # Palautetaan takaisin rekisteröitymislomakkeelle
        
        # Tarkistetaan, onko käyttäjänimi jo käytössä
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Käyttäjätunnus on jo käytössä')
            return redirect(url_for('register'))  # Jos käyttäjätunnus löytyy, palautetaan rekisteröitymislomakkeelle

        # Suolataan salasana ennen tallentamista
        hashed_password = generate_password_hash(password1)

        # Luodaan uusi käyttäjä ja tallennetaan tietokantaan
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Käyttäjä luotu onnistuneesti!')
        return redirect(url_for('login'))  # Siirretään kirjautumissivulle
    return render_template('register.html')

# Kirjautumissivu
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Haetaan käyttäjä tietokannasta
        user = User.query.filter_by(username=username).first()
        
        # Tarkistetaan, että salasana on oikea
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id  # Tallennetaan käyttäjän ID sessioniin
            flash('Tervetuloa takaisin!')
            return redirect(url_for('movies'))  # Ohjataan elokuvat-sivulle
        else:
            flash('Virheellinen tunnus tai salasana')
            return redirect(url_for('login'))  # Jos salasana on väärin, palautetaan kirjautumissivulle
    return render_template('login.html')

# Elokuvat-sivu (esimerkki)
@app.route('/movies', methods=['GET', 'POST'])
def movies():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    
    # Jos käyttäjä tekee haun
    if request.method == 'POST':
        search_query = request.form['search']
        movies = Movie.query.filter(
            Movie.user_id == user_id,
            Movie.title.ilike(f"%{search_query}%")  # Hakee osittaisia osumia
        ).all()
    else:
        movies = Movie.query.filter_by(user_id=user_id).all()

    return render_template('movies.html', movies=movies)

@app.route('/delete_movie/<int:movie_id>')
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Elokuva poistettu onnistuneesti!')
    return redirect(url_for('movies'))

@app.route('/edit_movie/<int:movie_id>', methods=['GET', 'POST'])
def edit_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    
    if request.method == 'POST':
        movie.title = request.form['title']
        movie.genre = request.form['genre']
        movie.year = request.form['year']
        
        db.session.commit()
        flash('Elokuva päivitetty onnistuneesti!')
        return redirect(url_for('movies'))  # Palataan elokuvat-sivulle
    
    return render_template('edit_movie.html', movie=movie)


# Uloskirjautumissivu
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Poistetaan käyttäjän ID sessionista
    flash('Olet kirjautunut ulos')
    return redirect(url_for('login'))  # Ohjataan takaisin kirjautumissivulle

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if request.method == 'POST':
        title = request.form['title']
        genre = request.form['genre']
        year = request.form['year']
        
        # Luodaan uusi elokuva ja tallennetaan tietokantaan
        new_movie = Movie(title=title, genre=genre, year=year, user_id=session['user_id'])
        db.session.add(new_movie)
        db.session.commit()
        
        flash('Elokuva lisätty onnistuneesti!')
        return redirect(url_for('movies'))  # Palataan elokuvat-sivulle
    return render_template('add_movie.html')

# Käynnistetään sovellus
if __name__ == '__main__':
    with app.app_context():  # Asetetaan sovelluksen konteksti
        db.create_all()  # Luo tietokannan taulut
    app.run(debug=True)
