from app.models import get_kompass


def mitglied_zu_gruppe_hinzufuegen(gruppe_id, mitglied_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO mitglied_jugendgruppen (mitglied_id, jugendgruppe_id)
            VALUES (?, ?)
            """,
            (mitglied_id, gruppe_id),
        )


def gruppenleiter_zu_gruppe_hinzufuegen(gruppe_id, leiter_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO gruppenleiter_jugendgruppen (gruppenleiter_id, jugendgruppe_id)
            VALUES (?, ?)
            """,
            (leiter_id, gruppe_id),
        )


def mitglied_aus_gruppe_entfernen(gruppe_id, mitglied_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM mitglied_jugendgruppen
            WHERE jugendgruppe_id = ? AND mitglied_id = ?
        """,
            (gruppe_id, mitglied_id),
        )


def gruppenleiter_aus_gruppe_entfernen(gruppe_id, leiter_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM gruppenleiter_jugendgruppen
            WHERE jugendgruppe_id = ? AND gruppenleiter_id = ?
        """,
            (gruppe_id, leiter_id),
        )


def search_person(search_in, search_query):
    with get_kompass() as conn:
        cursor = conn.cursor()
        query = f"""
            SELECT id, vorname, nachname
            FROM {search_in}
            WHERE vorname LIKE ? OR nachname LIKE ?
            """
        cursor.execute(query, ("%" + search_query + "%", "%" + search_query + "%"))
        search_results = cursor.fetchall()

    return search_results


def get_gruppe(gruppe_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
                """SELECT id, name, wochentag, startzeit, endzeit FROM jugendgruppen WHERE id = ?""",
                (gruppe_id,),
            )
        gruppe = cursor.fetchone()

    return gruppe


def get_mitglieder(gruppe_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
                """
                SELECT m.id, m.vorname, m.nachname, m.geburtsdatum, e.telefon 
                FROM mitglieder m
                LEFT JOIN mitglied_erziehungsberechtigte me ON m.id = me.mitglied_id
                LEFT JOIN erziehungsberechtigte e ON me.erziehungsberechtigter_id = e.id
                WHERE m.id IN (SELECT mitglied_id FROM mitglied_jugendgruppen WHERE jugendgruppe_id = ?)
            """,
                (gruppe_id,),
            )
        mitglieder = cursor.fetchall()
    return mitglieder


def get_gruppenleiter(gruppe_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
                """SELECT g.id, g.vorname, g.nachname FROM gruppenleiter g JOIN gruppenleiter_jugendgruppen gj ON g.id = gj.gruppenleiter_id WHERE gj.jugendgruppe_id = ?""",
                (gruppe_id,),
            )
        gruppenleiter = cursor.fetchall()
    
    return gruppenleiter
