from app.models import get_kompass


def mitglied_zu_gruppe_hinzufuegen(gruppe_id, mitglied_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT
            OR IGNORE INTO mitglied_jugendgruppen (mitglied_id, jugendgruppe_id)
            VALUES
                (?, ?)
            """,
            (mitglied_id, gruppe_id),
        )


def gruppenleiter_zu_gruppe_hinzufuegen(gruppe_id, leiter_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT
            OR IGNORE INTO gruppenleiter_jugendgruppen (gruppenleiter_id, jugendgruppe_id)
            VALUES
                (?, ?)
            """,
            (leiter_id, gruppe_id),
        )


def mitglied_aus_gruppe_entfernen(gruppe_id, mitglied_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM mitglied_jugendgruppen
            WHERE
                jugendgruppe_id = ?
                AND mitglied_id = ?
            """,
            (gruppe_id, mitglied_id),
        )


def gruppenleiter_aus_gruppe_entfernen(gruppe_id, leiter_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM gruppenleiter_jugendgruppen
            WHERE
                jugendgruppe_id = ?
                AND gruppenleiter_id = ?
            """,
            (gruppe_id, leiter_id),
        )


def search_person(search_in, search_query):
    with get_kompass() as conn:
        cursor = conn.cursor()
        query = f"""
            SELECT
                id,
                vorname,
                nachname
            FROM
                {search_in}
            WHERE
                vorname LIKE ?
                OR nachname LIKE ?
            """
        cursor.execute(query, ("%" + search_query + "%", "%" + search_query + "%"))
        search_results = cursor.fetchall()

    return search_results


def get_gruppe(gruppe_id):
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
            WHERE
                id = ?
            """,
            (gruppe_id,),
        )
        gruppe = cursor.fetchone()

    return gruppe


def get_mitglieder(gruppe_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                m.id,
                m.vorname,
                m.nachname,
                m.geburtsdatum,
                e.telefon
            FROM
                mitglieder m
                LEFT JOIN mitglied_erziehungsberechtigte me ON m.id = me.mitglied_id
                LEFT JOIN erziehungsberechtigte e ON me.erziehungsberechtigter_id = e.id
            WHERE
                m.id IN (
                    SELECT
                        mitglied_id
                    FROM
                        mitglied_jugendgruppen
                    WHERE
                        jugendgruppe_id = ?
                )
            """,
            (gruppe_id,),
        )
        mitglieder = cursor.fetchall()
    return mitglieder


def get_gruppenleiter(gruppe_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                g.id,
                g.vorname,
                g.nachname,
                g.telefon
            FROM
                gruppenleiter g
                JOIN gruppenleiter_jugendgruppen gj ON g.id = gj.gruppenleiter_id
            WHERE
                gj.jugendgruppe_id = ?
            """,
            (gruppe_id,),
        )
        gruppenleiter = cursor.fetchall()

    return gruppenleiter


def get_query_vars(person_typ):
    if person_typ == "gruppenleiter":
        table = "anwesenheit_leiter"
        query_id = "gruppenleiter_id"
    elif person_typ == "mitglied":
        table = "anwesenheit"
        query_id = "mitglied_id"
    return table, query_id


def get_anwesenheit(gruppe_id, person_typ):
    anwesenheitshistorie = {}
    alle_daten = []
    table, query_id = get_query_vars(person_typ)

    query = f"""
            SELECT
                {query_id},
                datum,
                anwesend
            FROM
                {table}
            WHERE
                gruppe_id = ?
            ORDER BY
                datum
            """

    with get_kompass() as conn:
        cursor = conn.cursor()
        cursor.execute(
            query,
            (gruppe_id,),
        )
        for row in cursor.fetchall():
            person_id, datum, anwesend = (
                row[query_id],
                row["datum"],
                row["anwesend"],
            )
            if person_id not in anwesenheitshistorie:
                anwesenheitshistorie[person_id] = {}
            anwesenheitshistorie[person_id][datum] = anwesend
            alle_daten.append(datum)
    return alle_daten, anwesenheitshistorie


def update_anwesenheit(gruppe_id, person_typ, person_list, request, daten):
    table, query_id = get_query_vars(person_typ)

    query = f"""
            INSERT
            OR REPLACE INTO {table} ({query_id}, gruppe_id, datum, anwesend)
            VALUES
                (?, ?, ?, ?)
            """
    with get_kompass() as conn:
        cursor = conn.cursor()

        for person in person_list:
            for datum in daten:
                field = f"{person_typ}_{person['id']}_{datum}"
                anwesend = field in request.form
                cursor.execute(query, (person["id"], gruppe_id, datum, anwesend))

def new_day(gruppe_id, datum):
    with get_kompass() as conn:
        cursor = conn.cursor()
        mitglieder = get_mitglieder(gruppe_id=gruppe_id)
        gruppenleiter = get_gruppenleiter(gruppe_id=gruppe_id)

        for mitglied in mitglieder:
            cursor.execute(
                """
                INSERT OR IGNORE
                INTO 
                    anwesenheit
                    (mitglied_id, gruppe_id, datum, anwesend)
                VALUES 
                    (?, ?, ?, 0)
                """, 
                (mitglied["id"], gruppe_id, datum))

        for leiter in gruppenleiter:
            cursor.execute(
                """
                INSERT OR IGNORE
                INTO 
                    anwesenheit_leiter
                    (gruppenleiter_id, gruppe_id, datum, anwesend)
                VALUES 
                    (?, ?, ?, 0)
                """, 
                (leiter["id"], gruppe_id, datum))
