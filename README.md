# Tikawe Leffalista

Tämä on elokuvatietokannan hallintasovellus, jossa käyttäjät voivat rekisteröityä, kirjautua sisään, lisätä elokuvia, muokata niitä, poistaa ja etsiä elokuvia.

## Ominaisuudet

- Käyttäjät voivat luoda tunnuksen ja kirjautua sisään
- Käyttäjät voivat lisätä, muokata ja poistaa elokuvia
- Elokuvia voi etsiä hakusanalla (pitäisi nyt toimia ja hakutoiminnolla voi myös hakea genren tai vuoden perusteella)
- Käyttäjät voivat kirjautua ulos

## Teknologiat

- Flask (Python Web Framework)
- SQLite (Tietokanta)
- HTML, CSS (Käyttöliittymä)


## Asennusohje

Luo virtuaaliympäristö:

`python3 -m venv venv`

Aktivoi virtuaaliympäristö:

Windows:

`venv\Scripts\activate`

Mac/Linux:

`source venv/bin/activate`

3. Asenna riippuvuudet
Asenna tarvittavat Python-kirjastot:

`pip install flask`

5. Luo tietokannan taulut
Sovelluksessa käytetään SQLite-tietokantaa. Luo tietokannan taulut ajamalla seuraava komento:

`python app.py`

Tai, jos haluat käyttää valmista SQL-tiedostoa:

`sqlite3 database.db < init.sql`

5. Suorita sovellus
Kun kaikki on asetettu, voit käynnistää sovelluksen seuraavalla komennolla:

`flask run`

Pääasiallinen tietokohde on elokuva ja toissijainen tietokohde on arvostelu (W.I.P).
