"""StayFlow auth maintenance utility.
Usage:
  python auth_tools.py repair
  python auth_tools.py bootstrap-admin
  python auth_tools.py confirm-email
"""
import getpass
from database import get_connection, init_db
from stayflow_auth import admin_get_user_by_email, admin_create_user, admin_update_user


def repair():
    email = input("Email to repair: ").strip().lower()
    auth_user = admin_get_user_by_email(email)
    if not auth_user:
        print("No Supabase Auth user found for that email.")
        return
    conn = get_connection()
    try:
        profile = conn.execute("SELECT * FROM users WHERE lower(email)=lower(%s)", (email,)).fetchone()
        if profile:
            conn.execute("UPDATE users SET auth_user_id=%s WHERE id=%s", (str(auth_user.id), profile["id"]))
            conn.commit()
            print(f"Re-linked existing {profile['role']} profile to Supabase Auth.")
        else:
            username = ((getattr(auth_user, 'user_metadata', None) or {}).get('username') or email.split('@')[0])[:80]
            base, candidate, n = username, username, 1
            while conn.execute("SELECT 1 FROM users WHERE username=%s", (candidate,)).fetchone():
                n += 1; candidate = f"{base}-{n}"
            conn.execute("INSERT INTO users(auth_user_id,username,role,email) VALUES(%s,%s,'guest',%s)", (str(auth_user.id), candidate, email))
            conn.commit()
            print("Created missing guest profile and linked it to Supabase Auth.")
    finally:
        conn.close()



def confirm_email():
    email = input("Email to confirm: ").strip().lower()
    auth_user = admin_get_user_by_email(email)
    if not auth_user:
        print("No Supabase Auth user found for that email.")
        return
    admin_update_user(str(auth_user.id), {"email_confirm": True})
    print("Email confirmed in Supabase Auth. The user can now sign in with their existing password.")

def bootstrap_admin():
    email = input("Admin email: ").strip().lower()
    username = input("Admin name: ").strip()
    password = getpass.getpass("Admin password (8+ chars): ")
    if len(password) < 8: raise SystemExit("Password must be at least 8 characters.")
    existing = admin_get_user_by_email(email)
    auth_user = existing or admin_create_user(email, password, username, "admin").user
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE lower(email)=lower(%s)", (email,)).fetchone()
        if row:
            conn.execute("UPDATE users SET auth_user_id=%s, username=%s, role='admin' WHERE id=%s", (str(auth_user.id), username, row['id']))
        else:
            conn.execute("INSERT INTO users(auth_user_id,username,role,email) VALUES(%s,%s,'admin',%s)", (str(auth_user.id), username, email))
        conn.commit(); print("Admin profile ready. Sign in at /login.")
    finally: conn.close()

if __name__ == '__main__':
    import sys
    init_db()
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    if command == 'repair': repair()
    elif command == 'bootstrap-admin': bootstrap_admin()
    elif command == 'confirm-email': confirm_email()
    else: print(__doc__)
