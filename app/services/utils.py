from app.models import get_kompass
import datetime


def heute():
    today = [
        "Montag",
        "Dienstag",
        "Mittwoch",
        "Donnerstag",
        "Freitag",
        "Samstag",
        "Sonntag",
    ][datetime.datetime.today().weekday()]
    return today


def jugendgruppen_preview():
    result = []

    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                name,
                wochentag,
                startzeit,
                endzeit
            FROM
                jugendgruppen
            ORDER BY
                CASE wochentag
                    WHEN 'Montag' THEN 1
                    WHEN 'Dienstag' THEN 2
                    WHEN 'Mittwoch' THEN 3
                    WHEN 'Donnerstag' THEN 4
                    WHEN 'Freitag' THEN 5
                    WHEN 'Samstag' THEN 6
                    WHEN 'Sonntag' THEN 7
                END
            """)
        gruppen = cursor.fetchall()
        for gruppe in gruppen:
            gruppe_id, name, wochentag, startzeit, endzeit = gruppe

            cursor.execute(
                """
                SELECT
                    g.vorname || ' ' || g.nachname
                FROM
                    gruppenleiter g
                    JOIN gruppenleiter_jugendgruppen gj ON g.id = gj.gruppenleiter_id
                WHERE
                    gj.jugendgruppe_id = ?
                """,
                (gruppe_id,),
            )
            gruppenleiter = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                SELECT
                    m.vorname || ' ' || m.nachname
                FROM
                    mitglieder m
                    JOIN mitglied_jugendgruppen mj ON m.id = mj.mitglied_id
                WHERE
                    mj.jugendgruppe_id = ?
                """,
                (gruppe_id,),
            )
            mitglieder = [row[0] for row in cursor.fetchall()]

            gruppe_dict = {
                "id": gruppe_id,
                "name": name,
                "wochentag": wochentag,
                "startzeit": startzeit,
                "endzeit": endzeit,
                "gruppenleiter": gruppenleiter,
                "mitglieder": mitglieder,
            }

            result.append(gruppe_dict)

    return result
