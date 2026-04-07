from app.models import get_accounts, get_kompass


def save_gruppenleiter(data, gruppen_leiter_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        if gruppen_leiter_id:
            cursor.execute(
                """
                UPDATE gruppenleiter
                SET
                    vorname = ?,
                    nachname = ?,
                    geburtsdatum = ?,
                    iban = ?,
                    bic = ?,
                    bank = ?,
                    telefon = ?,
                    gruppenrolle = ?,
                    vereinsrolle = ?
                WHERE
                    id = ?
                """,
                (
                    data["vorname"],
                    data["nachname"],
                    data["geburtsdatum"],
                    data["iban"],
                    data["bic"],
                    data["bank"],
                    data["telefon"],
                    data["gruppenrolle"],
                    data["vereinsrolle"],
                    gruppen_leiter_id,
                ),
            )

        else:
            cursor.execute(
                """
                INSERT INTO
                    gruppenleiter (
                    vorname,
                    nachname,
                    geburtsdatum,
                    iban,
                    bic,
                    bank,
                    telefon,
                    gruppenrolle,
                    vereinsrolle
                    )
                VALUES
                    (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    data["vorname"],
                    data["nachname"],
                    data["geburtsdatum"],
                    data["iban"],
                    data["bic"],
                    data["bank"],
                    data["telefon"],
                    data["gruppenrolle"],
                    data["vereinsrolle"],
                ),
            )


def update_account_status(account_id, status):
    with get_accounts() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE accounts
            SET
                status = ?
            WHERE
                id = ?
            AND role != '4'
            """,
            (status, account_id),
        )


def delete_account(account_id):
    with get_accounts() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM accounts
            WHERE
                id = ?
                AND role != '4'
            """,
            (account_id,),
        )


def change_account_role(account_id, new_role):
    with get_accounts() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE accounts
            SET
                role = ?
            WHERE
                id = ?
                AND role != '4'
            """,
            (new_role, account_id),
        )


def get_all_accounts():
    with get_accounts() as conn:
        cursor = conn.cursor()
        accounts = cursor.execute(
            """
            SELECT
                id,
                uname,
                status,
                role
            FROM
                accounts
            ORDER BY
                id
            """
        ).fetchall()
        return accounts


def get_gruppenleiter(gruppenleiter_id):
    with get_kompass() as conn:
        cursor = conn.cursor()
        gruppenleiter = cursor.execute(
            """
            SELECT
                *
            FROM
                gruppenleiter
            WHERE
                id = ?
            """,
            (gruppenleiter_id,)
        ).fetchone()
        return gruppenleiter


def get_all_gruppenleiter():
    with get_kompass() as conn:
        cursor = conn.cursor()

        gruppenleiter = cursor.execute("""
            SELECT
                gl.id,
                gl.vorname,
                gl.nachname,
                gl.geburtsdatum,
                gl.iban,
                gl.bic,
                gl.bank,
                gl.telefon,
                gl.gruppenrolle,
                gl.vereinsrolle,
                GROUP_CONCAT (jg.name, ', ') AS jugendgruppen
            FROM
                gruppenleiter gl
                LEFT JOIN gruppenleiter_jugendgruppen gj ON gl.id = gj.gruppenleiter_id
                LEFT JOIN jugendgruppen jg ON gj.jugendgruppe_id = jg.id
            GROUP BY
                gl.id
            ORDER BY
                gl.nachname
            """).fetchall()

        return gruppenleiter
