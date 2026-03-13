from flask import Blueprint
from flask import session, redirect, render_template, abort, request, url_for
import datetime
from app.models import get_kompass
from app.utils import jugendgruppen_preview
from flask import jsonify
import pandas as pd
from flask import send_file
from io import BytesIO
from app.routes.auth import check_user
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter
gruppen_bp = Blueprint('gruppen', __name__)


@gruppen_bp.route("/gruppen", methods=["GET", "POST"])
def gruppen():
    if not check_user(1):
        return redirect(url_for("auth.login"))

    gruppen = jugendgruppen_preview()
    return render_template("gruppen.html", gruppen=gruppen)


@gruppen_bp.route('/search_mitglied', methods=['GET'])
def search_mitglied():
    if not check_user(1):
        return redirect(url_for("auth.login"))

    search_query = request.args.get('query', '')
    conn = get_kompass()
    cursor = conn.cursor()
    cursor.execute("""SELECT id, vorname, nachname FROM mitglieder WHERE vorname LIKE ? OR nachname LIKE ?""", ('%' + search_query + '%', '%' + search_query + '%'))
    search_results_mitglieder = cursor.fetchall()
    conn.close()
    return jsonify({"results": [{"id": row[0], "vorname": row[1], "nachname": row[2]} for row in search_results_mitglieder]})


@gruppen_bp.route('/search_gruppenleiter', methods=['GET'])
def search_gruppenleiter():
    if not check_user(1):
        return redirect(url_for("auth.login"))

    search_query = request.args.get('query', '')
    conn = get_kompass()
    cursor = conn.cursor()
    cursor.execute("""SELECT id, vorname, nachname FROM gruppenleiter WHERE vorname LIKE ? OR nachname LIKE ?""", ('%' + search_query + '%', '%' + search_query + '%'))
    search_results_gruppenleiter = cursor.fetchall()
    conn.close()
    return jsonify({"results": [{"id": row[0], "vorname": row[1], "nachname": row[2]} for row in search_results_gruppenleiter]})


@gruppen_bp.route("/gruppen/<int:gruppe_id>", methods=["GET", "POST"])
def gruppe_detail(gruppe_id):
    if not check_user(1):
        return redirect(url_for("auth.login"))

    if (not check_user(2)) and request.method == "POST":
        return redirect(url_for("auth.login"))

    conn = get_kompass()
    cursor = conn.cursor()

    # existiert die aufgerufene Gruppe?
    cursor.execute("""
SELECT id, name, wochentag, startzeit, endzeit
FROM jugendgruppen
WHERE id = ?
""", (gruppe_id,))
    gruppe = cursor.fetchone()
    if not gruppe:
        conn.close()
        abort(404)

    today = datetime.datetime.today()
    today_name = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"][today.weekday()]

    cursor.execute("""SELECT g.id, g.vorname, g.nachname FROM gruppenleiter g JOIN gruppenleiter_jugendgruppen gj ON g.id = gj.gruppenleiter_id WHERE gj.jugendgruppe_id = ?""", (gruppe_id,))
    gruppenleiter = cursor.fetchall()
    cursor.execute("""
        SELECT m.id, m.vorname, m.nachname, m.geburtsdatum, e.telefon 
        FROM mitglieder m
        LEFT JOIN mitglied_erziehungsberechtigte me ON m.id = me.mitglied_id
        LEFT JOIN erziehungsberechtigte e ON me.erziehungsberechtigter_id = e.id
        WHERE m.id IN (SELECT mitglied_id FROM mitglied_jugendgruppen WHERE jugendgruppe_id = ?)
    """, (gruppe_id,))
    mitglieder = cursor.fetchall()

    anwesenheitheute = {}
    anwesenheitshistorie = {}
    gruppenleiter_anwesenheitheute = {}
    gruppenleiter_anwesenheithistorie = {}
    alle_daten = set()

    # durchschnittliches alter
    total_age = 0
    count = 0

    for mitglied in mitglieder:
        geburtsdatum = datetime.datetime.strptime(mitglied["geburtsdatum"], "%Y-%m-%d") # Das Geburtsdatum
        if geburtsdatum:
            age = today.year - geburtsdatum.year - ((today.month, today.day) < (geburtsdatum.month, geburtsdatum.day))
            total_age += age
            count += 1

    avg_age = int(total_age / count if count > 0 else 0)

    if gruppe["wochentag"] == today_name:
        if request.method == "POST":
            for mitglied in mitglieder:
                anwesend = request.form.get(f"mitglied_{mitglied[0]}") == "on"
                cursor.execute("""INSERT OR REPLACE INTO anwesenheit (mitglied_id, gruppe_id, datum, anwesend) VALUES (?, ?, ?, ?)""", (mitglied[0], gruppe_id, today.date(), anwesend))
            for gl in gruppenleiter:
                anwesend = request.form.get(f"gruppenleiter_{gl[0]}") == "on"
                cursor.execute("""INSERT OR REPLACE INTO anwesenheit_leiter (gruppenleiter_id, gruppe_id, datum, anwesend) VALUES (?, ?, ?, ?)""", (gl[0], gruppe_id, today.date(), anwesend))

            conn.commit()

        cursor.execute("""SELECT mitglied_id, anwesend FROM anwesenheit WHERE gruppe_id = ? AND datum = ?""", (gruppe_id, today.date()))
        anwesenheitheute = {row[0]: bool(row[1]) for row in cursor.fetchall()}

        cursor.execute("""SELECT gruppenleiter_id, anwesend FROM anwesenheit_leiter WHERE gruppe_id = ? AND datum = ?""", (gruppe_id, today.date()))
        gruppenleiter_anwesenheitheute = {row[0]: bool(row[1]) for row in cursor.fetchall()}

    cursor.execute("""SELECT mitglied_id, datum, anwesend FROM anwesenheit WHERE gruppe_id = ? ORDER BY datum""", (gruppe_id,))
    for row in cursor.fetchall():
        mitglied_id, datum, anwesend = row
        alle_daten.add(datum)
        if mitglied_id not in anwesenheitshistorie:
            anwesenheitshistorie[mitglied_id] = {}
        anwesenheitshistorie[mitglied_id][datum] = anwesend

    cursor.execute("""SELECT gruppenleiter_id, datum, anwesend FROM anwesenheit_leiter WHERE gruppe_id = ?ORDER BY datum""", (gruppe_id,))
    for row in cursor.fetchall():
        gruppenleiter_id, datum, anwesend = row
        alle_daten.add(datum)
        if gruppenleiter_id not in gruppenleiter_anwesenheithistorie:
            gruppenleiter_anwesenheithistorie[gruppenleiter_id] = {}
        gruppenleiter_anwesenheithistorie[gruppenleiter_id][datum] = anwesend

    conn.close()

    return render_template(
        "gruppe_detail.html",
        today_name=today_name,
        gruppe=gruppe,
        mitglieder=mitglieder,
        anwesenheitheute=anwesenheitheute,
        anwesenheitshistorie=anwesenheitshistorie,
        alle_daten=sorted(alle_daten),
        gruppenleiter=gruppenleiter,
        gruppenleiter_anwesenheitheute=gruppenleiter_anwesenheitheute,
        gruppenleiter_anwesenheithistorie=gruppenleiter_anwesenheithistorie,
        avg_age=avg_age
    )


@gruppen_bp.route("/gruppen/neue", methods=["POST"])
def neue_gruppe():
    if not check_user(3):
        return redirect(url_for("auth.login"))

    name = request.form.get("name")
    beschreibung = request.form.get("beschreibung")
    wochentag = request.form.get("wochentag")
    startzeit = request.form.get("startzeit")
    endzeit = request.form.get("endzeit")

    if not name or not wochentag or not startzeit or not endzeit:
        return "Fehlende Daten!", 400

    conn = get_kompass()
    cursor = conn.cursor()
    cursor.execute("""
INSERT INTO jugendgruppen (name, beschreibung, wochentag, startzeit, endzeit)
VALUES (?, ?, ?, ?, ?)
""", (name, beschreibung, wochentag, startzeit, endzeit))
    conn.commit()
    conn.close()

    return redirect(url_for("gruppen.gruppen"))


@gruppen_bp.route("/gruppen/<int:gruppe_id>/loeschen", methods=["POST"])
def gruppe_loeschen(gruppe_id):
    if not check_user(3):
        return redirect(url_for("auth.login"))

    conn = get_kompass()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jugendgruppen WHERE id = ?", (gruppe_id,))
    cursor.execute("DELETE FROM mitglied_jugendgruppen WHERE jugendgruppe_id = ?", (gruppe_id,))
    cursor.execute("DELETE FROM gruppenleiter_jugendgruppen WHERE jugendgruppe_id = ?", (gruppe_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("gruppen.gruppen"))


@gruppen_bp.route("/gruppen/<int:gruppe_id>/mitglied/<int:mitglied_id>", methods=["POST"])
def mitglied_zu_gruppe(gruppe_id, mitglied_id):
    print(1)
    if not check_user(3):
        return redirect(url_for("auth.login"))

    conn = get_kompass()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM mitglied_jugendgruppen 
        WHERE mitglied_id = ? AND jugendgruppe_id = ?
    """, (mitglied_id, gruppe_id))

    existing = cursor.fetchone()

    if not existing:
        cursor.execute("""
            INSERT INTO mitglied_jugendgruppen (mitglied_id, jugendgruppe_id)
            VALUES (?, ?)
        """, (mitglied_id, gruppe_id))
        conn.commit()
        conn.close()

    return redirect(url_for("gruppen.gruppe_detail", gruppe_id=gruppe_id))


@gruppen_bp.route("/gruppenleiter_zu_gruppe/<int:gruppe_id>/<int:gruppenleiter_id>", methods=["POST"])
def gruppenleiter_zu_gruppe(gruppe_id, gruppenleiter_id):
    if not check_user(2):
        return redirect(url_for("auth.login"))

    conn = get_kompass()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 1 FROM gruppenleiter_jugendgruppen 
        WHERE gruppenleiter_id = ? AND jugendgruppe_id = ?
    """, (gruppenleiter_id, gruppe_id))
    existing = cursor.fetchone()

    if not existing:
        cursor.execute("""
            INSERT INTO gruppenleiter_jugendgruppen (gruppenleiter_id, jugendgruppe_id)
            VALUES (?, ?)
        """, (gruppenleiter_id, gruppe_id))
        conn.commit()

    conn.close()

    return redirect(url_for("gruppen.gruppe_detail", gruppe_id=gruppe_id))


@gruppen_bp.route("/gruppen/<int:gruppe_id>/mitglied/<int:mitglied_id>/entfernen", methods=["POST"])
def mitglied_entfernen(gruppe_id, mitglied_id):
    if not check_user(3):
        return redirect(url_for("auth.login"))
    conn = get_kompass()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM mitglied_jugendgruppen WHERE jugendgruppe_id = ? AND mitglied_id = ?", (gruppe_id, mitglied_id))
    conn.commit()
    conn.close()

    return redirect(url_for('gruppen.gruppe_detail', gruppe_id=gruppe_id))


@gruppen_bp.route("/gruppen/<int:gruppe_id>/gruppenleiter/<int:gruppenleiter_id>/entfernen", methods=["POST"])
def gruppenleiter_entfernen(gruppe_id, gruppenleiter_id):
    if not check_user(3):
        return redirect(url_for("auth.login"))

    conn = get_kompass()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM gruppenleiter_jugendgruppen WHERE jugendgruppe_id = ? AND gruppenleiter_id = ?", (gruppe_id, gruppenleiter_id))
    conn.commit()
    conn.close()

    return redirect(url_for('gruppen.gruppe_detail', gruppe_id=gruppe_id))

@gruppen_bp.route("/gruppen/<int:gruppe_id>/download_attendance", methods=["GET"])
def download_attendance(gruppe_id):
    if not check_user(3):
        return redirect(url_for("auth.login"))

    conn = get_kompass()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT vorname, nachname, datum, anwesend 
        FROM anwesenheit 
        JOIN mitglieder m on mitglied_id = m.id 
        WHERE gruppe_id = ?
    """, (gruppe_id,))
    anwesenheit_mitglieder = cursor.fetchall()

    cursor.execute("""
        SELECT vorname, nachname, datum, anwesend 
        FROM anwesenheit_leiter 
        JOIN gruppenleiter gl on gruppenleiter_id = gl.id 
        WHERE gruppe_id = ?
    """, (gruppe_id,))
    anwesenheit_gruppenleiter = cursor.fetchall()

    conn.close()

    df_m = pd.DataFrame(
        anwesenheit_mitglieder,
        columns=["vorname", "nachname", "datum", "anwesend"]
    )

    df_l = pd.DataFrame(
        anwesenheit_gruppenleiter,
        columns=["vorname", "nachname", "datum", "anwesend"]
    )

    df_m["Rolle"] = "Mitglied"
    df_l["Rolle"] = "Gruppenleiter"

    df = pd.concat([df_m, df_l])

    df["Person"] = df["vorname"] + " " + df["nachname"]
    df["datum"] = pd.to_datetime(df["datum"])

    table = pd.pivot_table(
        df,
        index=["Rolle", "Person"],
        columns="datum",
        values="anwesend",
        aggfunc="max"
    )

    table = table.fillna(0).replace({1: "X", 0: ""})
    table = table.sort_index(axis=1)

    table.columns = table.columns.strftime("%d.%m.%Y")

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        table.to_excel(writer, sheet_name="Anwesenheit")

        workbook = writer.book
        sheet = writer.sheets["Anwesenheit"]

        for cell in sheet[1]:
            cell.font = Font(bold=True)

        for cell in sheet["A"]:
            if cell.row != 1 and cell.value in ["Mitglied", "Gruppenleiter"]:
                cell.font = Font(bold=True)

        for row in sheet.iter_rows(min_row=2, min_col=3):
            for cell in row:
                cell.alignment = Alignment(horizontal="center")

        for col in sheet.columns:
            max_length = 0
            col_letter = get_column_letter(col[0].column)

            for cell in col:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass

            sheet.column_dimensions[col_letter].width = max_length + 3

        sheet.freeze_panes = "C2"

        sheet.auto_filter.ref = sheet.dimensions

    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f"anwesenheit_gruppe_{gruppe_id}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
