# Tikawe Leffalista

Tämä on elokuvatietokannan hallintasovellus, jossa käyttäjät voivat rekisteröityä, kirjautua sisään, lisätä elokuvia, muokata niitä, poistaa ja etsiä elokuvia.

## Ominaisuudet

- Käyttäjät voivat luoda tunnuksen ja kirjautua sisään
- Käyttäjät voivat lisätä, muokata ja poistaa elokuvia
- Elokuvia voi etsiä hakusanalla 
- Käyttäjät voivat kirjautua ulos
- Käyttäjäsivut toimivat ja näyttävät tilastoja sekä käyttäjän omat elokuvat
- Elokuville voi lisätä useita luokkia, jotka tallentuvat ja näkyvät käyttöliittymässä
- Muiden käyttäjien elokuviin voi lisätä kommentteja


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

Asenna tarvittavat Python-kirjastot:

`pip install flask`

Luo tietokannan taulut
Sovelluksessa käytetään SQLite-tietokantaa. Luo tietokannan taulut ajamalla seuraava komento:

`python app.py`

5. Suorita sovellus
Kun kaikki on asetettu, voit käynnistää sovelluksen seuraavalla komennolla:

`flask run`

Pääasiallinen tietokohde on elokuva ja toissijainen tietokohde on arvostelu (W.I.P).
