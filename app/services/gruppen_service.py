from app.models import get_kompass


def neue_gruppe_erstellen(data):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO
                jugendgruppen (name, beschreibung, wochentag, startzeit, endzeit)
            VALUES
                (?, ?, ?, ?, ?)
            """,
            (
                data["name"],
                data["beschreibung"],
                data["wochentag"],
                data["startzeit"],
                data["endzeit"],
            ),
        )


def loesche_gruppe(gruppe_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jugendgruppen WHERE id = ?", (gruppe_id,))
        cursor.execute(
            """
            DELETE FROM mitglied_jugendgruppen
            WHERE
                jugendgruppe_id = ?
            """,
            (gruppe_id,)
        )
        cursor.execute(
            """
            DELETE FROM gruppenleiter_jugendgruppen
            WHERE
                jugendgruppe_id = ?
            """,
            (gruppe_id,),
        )
