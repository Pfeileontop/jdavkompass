import random
import datetime
from app.models import get_kompass

# Sample data
first_names = ["Anna", "Lukas", "Marie", "Paul", "Emma", "Jonas", "Sophia", "Finn"]
last_names = ["Müller", "Schmidt", "Weber", "Fischer", "Meier", "Wagner", "Becker", "Hoffmann"]
streets = ["Hauptstraße", "Bahnhofstraße", "Gartenweg", "Schulstraße", "Ringstraße", "Wiesenweg", "Bergstraße", "Dorfstraße"]
cities = ["Hildesheim", "Göttingen", "Braunschweig", "Hannover", "Osnabrück", "Bremen", "Kassel", "Magdeburg"]

def random_date(start_year=2005, end_year=2015):
    start = datetime.date(start_year, 1, 1)
    end = datetime.date(end_year, 12, 31)
    delta = end - start
    return start + datetime.timedelta(days=random.randint(0, delta.days))

def generate_8_mitglieder():
    with get_kompass() as conn:
        cursor = conn.cursor()
        for _ in range(8):
            # Member data
            vorname = random.choice(first_names)
            nachname = random.choice(last_names)
            geburtsdatum = random_date().strftime("%Y-%m-%d")
            geschlecht = random.choice(["m", "w"])
            unterschrift = "ja"

            # Address data
            strasse = random.choice(streets)
            hausnummer = str(random.randint(1, 50))
            plz = str(random.randint(30000, 39999))
            ort = random.choice(cities)

            # Guardian data
            eb_vorname = random.choice(first_names)
            eb_nachname = random.choice(last_names)
            eb_email = f"{eb_vorname.lower()}.{eb_nachname.lower()}@example.com"
            eb_telefon = f"0{random.randint(1500000000, 1599999999)}"

            # Insert address
            cursor.execute(
                "INSERT INTO adressen (strasse, hausnummer, plz, ort) VALUES (?, ?, ?, ?)",
                (strasse, hausnummer, plz, ort)
            )
            adresse_id = cursor.lastrowid

            # Insert guardian
            cursor.execute(
                "INSERT INTO erziehungsberechtigte (vorname, nachname, email, telefon, adresse_id) VALUES (?, ?, ?, ?, ?)",
                (eb_vorname, eb_nachname, eb_email, eb_telefon, adresse_id)
            )
            eb_id = cursor.lastrowid

            # Insert member
            cursor.execute(
                """
                INSERT INTO mitglieder (vorname, nachname, geburtsdatum, geschlecht, adresse_id, unterschrift)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (vorname, nachname, geburtsdatum, geschlecht, adresse_id, unterschrift)
            )
            mitglied_id = cursor.lastrowid

            # Link member to guardian
            cursor.execute(
                "INSERT INTO mitglied_erziehungsberechtigte (mitglied_id, erziehungsberechtigter_id, rolle) VALUES (?, ?, ?)",
                (mitglied_id, eb_id, "erziehungsberechtigter")
            )

        conn.commit()
        print("8 Mitglieder erfolgreich generiert!")

# Run the generator
#generate_8_mitglieder()

import random
import datetime
from app.models import get_kompass

def generate_anwesenheit(days_back=30):
    """
    Generate random attendance for members and group leaders
    over the last `days_back` days.
    """
    today = datetime.date.today()

    with get_kompass() as conn:
        cursor = conn.cursor()

        # Fetch all members
        cursor.execute("SELECT id FROM mitglieder")
        mitglieder = [row["id"] for row in cursor.fetchall()]

        # Fetch all groups
        cursor.execute("SELECT id FROM jugendgruppen")
        gruppen = [row["id"] for row in cursor.fetchall()]

        # Fetch all group leaders
        cursor.execute("SELECT id FROM gruppenleiter")
        gruppenleiter = [row["id"] for row in cursor.fetchall()]

        # Generate attendance for each group, member, and leader
        for gruppe_id in gruppen:
            for delta in range(days_back):
                datum = today - datetime.timedelta(days=delta)
                # Randomly decide if day is a session (simulate weekday matching)
                if random.random() < 0.7:  # 70% chance this group met
                    # Members
                    for mitglied_id in mitglieder:
                        anwesend = random.choice([0, 1])
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO anwesenheit (person_id, gruppe_id, person_typ, datum, anwesend)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (mitglied_id, gruppe_id, "mitglied", datum, anwesend)
                        )

                    # Group leaders
                    for gl_id in gruppenleiter:
                        anwesend = random.choice([0, 1])
                        cursor.execute(
                            """
                            INSERT OR REPLACE INTO anwesenheit (person_id, gruppe_id, person_typ, datum, anwesend)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (gl_id, gruppe_id, "gruppenleiter", datum, anwesend)
                        )

        conn.commit()
        print(f"Attendance data generated for the last {days_back} days.")

# Run it
generate_anwesenheit(days_back=14)  # Example: generate 2 weeks of data