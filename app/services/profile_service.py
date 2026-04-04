from app.models import get_accounts
from werkzeug.security import generate_password_hash


def update_password(user_id, new_password):
    with get_accounts() as conn:
        cursor = conn.cursor()
        hashed = generate_password_hash(new_password)
        cursor.execute("UPDATE accounts SET password = ? WHERE id = ?", (hashed, user_id))


def get_account(current_user):
    with get_accounts() as conn:
        cursor = conn.cursor()
        user = cursor.execute(
            "SELECT id, uname, password FROM accounts WHERE id = ?", (current_user.id,)
        ).fetchone()
    return user
