import os
from supabase import create_client

URL = os.getenv("SUPABASE_URL", "").strip()
ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "").strip()
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()


def _client(key):
    if not URL or not key:
        raise RuntimeError("Supabase environment variables are not configured.")
    return create_client(URL, key)


def sign_up(email, password, username):
    """Create a self-service guest on the trusted Flask server.

    Admin create_user with email_confirm=True deliberately avoids Supabase's
    confirmation-email quota. The caller never controls the role.
    """
    return admin_create_user(email, password, username, "guest")


def sign_in(email, password):
    return _client(ANON_KEY).auth.sign_in_with_password({"email": email, "password": password})


def admin_get_user_by_email(email):
    """Return a Supabase Auth user with this email, or None. Server-only."""
    page = 1
    while page <= 20:
        response = _client(SERVICE_ROLE_KEY).auth.admin.list_users(page=page, per_page=100)
        users = getattr(response, "users", response if isinstance(response, list) else []) or []
        for user in users:
            if (getattr(user, "email", "") or "").lower() == email.lower():
                return user
        if len(users) < 100:
            break
        page += 1
    return None


def admin_create_user(email, password, username, role):
    if role not in {"admin", "manager", "guest"}:
        raise ValueError("Invalid role")
    return _client(SERVICE_ROLE_KEY).auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"username": username, "role": role},
    })


def admin_update_user(auth_user_id, attrs):
    return _client(SERVICE_ROLE_KEY).auth.admin.update_user_by_id(str(auth_user_id), attrs)


def admin_delete_user(auth_user_id):
    if auth_user_id:
        return _client(SERVICE_ROLE_KEY).auth.admin.delete_user(str(auth_user_id))
