"""
Das hier startet die Flask App fuer jdavkompass.
Das Skript initialisiert die Flask App in dem create_app() von
app/__init__.py aufgerufen wird.
In Production sollte ein WSGI Server benutzt werden
und Debug mode ausgeschaltet werden.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
