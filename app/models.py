import sqlite3
from contextlib import contextmanager

from flask_login import UserMixin
from werkzeug.security import generate_password_hash


def init_db():
    statements_kompass = [
        """
        CREATE TABLE IF NOT EXISTS mitglieder (
            id INTEGER PRIMARY KEY,
            vorname TEXT not NULL,
            nachname TEXT not NULL,
            geburtsdatum DATE not NULL,
            geschlecht TEXT,
            adresse_id INTEGER,
            bilder BOOLEAN,
            unterschrift TEXT,
            mitgliedsnummer TEXT,
            FOREIGN KEY (adresse_id) REFERENCES adressen(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS adressen (
            id INTEGER PRIMARY KEY,
            strasse TEXT NOT NULL,
            hausnummer TEXT NOT NULL,
            plz TEXT NOT NULL,
            ort TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS erziehungsberechtigte (
            id INTEGER PRIMARY KEY,
            vorname TEXT NOT NULL,
            nachname TEXT NOT NULL,
            email TEXT NOT NULL,
            telefon TEXT NOT NULL,
            adresse_id INTEGER,
            FOREIGN KEY (adresse_id) REFERENCES adressen(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS mitglied_erziehungsberechtigte (
            mitglied_id INTEGER,
            erziehungsberechtigter_id INTEGER,
            rolle TEXT,
            PRIMARY KEY (mitglied_id, erziehungsberechtigter_id),
            FOREIGN KEY (mitglied_id) REFERENCES mitglieder(id),
            FOREIGN KEY (erziehungsberechtigter_id) REFERENCES erziehungsberechtigte(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS jugendgruppen (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            beschreibung TEXT,
            wochentag TEXT NOT NULL,
            startzeit TIME NOT NULL,
            endzeit TIME NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS gruppenleiter (
            id INTEGER PRIMARY KEY,
            vorname TEXT NOT NULL,
            nachname TEXT NOT NULL,
            geburtsdatum DATE NOT NULL,
            iban TEXT NOT NULL,
            bic TEXT NOT NULL,
            bank TEXT NOT NULL,
            telefon TEXT NOT NULL,
            gruppenrolle TEXT NOT NULL, -- Jugendleiter, Helfer
            vereinsrolle TEXT NOT NULL  -- keine, Jugendausschuss, Jugendreferent
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS gruppenleiter_jugendgruppen (
            gruppenleiter_id INTEGER,
            jugendgruppe_id INTEGER,
            PRIMARY KEY (gruppenleiter_id, jugendgruppe_id),
            FOREIGN KEY (gruppenleiter_id) REFERENCES gruppenleiter(id),
            FOREIGN KEY (jugendgruppe_id) REFERENCES jugendgruppen(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS mitglied_jugendgruppen (
            mitglied_id INTEGER,
            jugendgruppe_id INTEGER,
            PRIMARY KEY (mitglied_id, jugendgruppe_id),
            FOREIGN KEY (mitglied_id) REFERENCES mitglieder(id),
            FOREIGN KEY (jugendgruppe_id) REFERENCES jugendgruppen(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS fortbildungen (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            datum DATE NOT NULL,
            gueltig_bis DATE
                );
        """,
        """
        CREATE TABLE IF NOT EXISTS gruppenleiter_fortbildungen (
            gruppenleiter_id INTEGER,
            fortbildung_id INTEGER,
            PRIMARY KEY (gruppenleiter_id, fortbildung_id),
            FOREIGN KEY (gruppenleiter_id) REFERENCES gruppenleiter(id),
            FOREIGN KEY (fortbildung_id) REFERENCES fortbildungen(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS anwesenheit (
            mitglied_id INTEGER,
            gruppe_id INTEGER,
            datum DATE NOT NULL,
            anwesend BOOLEAN NOT NULL,
            PRIMARY KEY (mitglied_id, gruppe_id, datum),
            FOREIGN KEY (mitglied_id) REFERENCES mitglieder(id),
            FOREIGN KEY (gruppe_id) REFERENCES jugendgruppen(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS anwesenheit_leiter (
            gruppenleiter_id INTEGER,
            gruppe_id INTEGER,
            datum DATE NOT NULL,
            anwesend BOOLEAN NOT NULL,
            PRIMARY KEY (gruppenleiter_id, gruppe_id, datum),
            FOREIGN KEY (gruppenleiter_id) REFERENCES gruppenleiter(id),
            FOREIGN KEY (gruppe_id) REFERENCES jugendgruppen(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS mitglieder_unapproved (
            id INTEGER PRIMARY KEY,
            vorname TEXT not NULL,
            nachname TEXT not NULL,
            geburtsdatum DATE not NULL,
            geschlecht TEXT,
            adresse_id INTEGER,
            unterschrift TEXT not NULL,
            mitgliedschaft BOOLEAN not NULL,
            beitraege BOOLEAN not NULL,
            datenschutz BOOLEAN not NULL,
            bilder BOOLEAN not NULL,
            richtigkeit BOOLEAN not NULL,
            FOREIGN KEY (adresse_id) REFERENCES adressen_unapproved(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS adressen_unapproved (
            id INTEGER PRIMARY KEY,
            strasse TEXT NOT NULL,
            hausnummer TEXT NOT NULL,
            plz TEXT NOT NULL,
            ort TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS erziehungsberechtigte_unapproved (
            id INTEGER PRIMARY KEY,
            vorname TEXT NOT NULL,
            nachname TEXT NOT NULL,
            email TEXT NOT NULL,
            telefon TEXT NOT NULL,
            adresse_id INTEGER,
            FOREIGN KEY (adresse_id) REFERENCES adressen_unapproved(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS mitglied_erziehungsberechtigte_unapproved (
            mitglied_id INTEGER,
            erziehungsberechtigter_id INTEGER,
            rolle TEXT,
            PRIMARY KEY (mitglied_id, erziehungsberechtigter_id),
            FOREIGN KEY (mitglied_id) REFERENCES mitglieder_unapproved(id),
            FOREIGN KEY (erziehungsberechtigter_id) REFERENCES erziehungsberechtigte_unapproved(id)
        );
        """,
    ]
    statements_accounts = [
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uname TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role INTEGER NOT NULL DEFAULT 1,
            status TEXT NOT NULL DEFAULT 'pending'
        );
        """
    ]

    with get_kompass() as conn:
        cursor = conn.cursor()
        for statement in statements_kompass:
            cursor.execute(statement)

    with get_accounts() as conn:
        cursor = conn.cursor()
        for statement in statements_accounts:
            cursor.execute(statement)

        existing = cursor.execute(
            """
            SELECT
                id
            FROM
                accounts
            WHERE
                uname = ?
            """,
            ("admin",)
        ).fetchone()

        if not existing:
            cursor.execute(
                """
                INSERT INTO accounts (uname, password, role, status)
                VALUES
                    (?, ?, ?, ?);
                """,
                ("admin", generate_password_hash("admin"), "4", "active"),
            )


@contextmanager
def get_accounts():
    conn = sqlite3.connect("app/db/accounts.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


@contextmanager
def get_kompass():
    conn = sqlite3.connect("app/db/kompass.db")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()


class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role
