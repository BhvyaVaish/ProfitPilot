import os
import json
import base64
import functools
from flask import request, jsonify, g

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

_firebase_app = None

def init_firebase_admin():
    """Initialize Firebase Admin SDK.

    Supports two credential sources (checked in order):
    1. FIREBASE_SERVICE_ACCOUNT_JSON env var — base64-encoded JSON string.
       Set this in the Vercel Dashboard for production.
    2. firebase-service-account.json file alongside this module (local dev).

    If neither is found the server still starts but all authenticated endpoints
    will fall back to unverified JWT decoding (development only).
    """
    global _firebase_app
    if _firebase_app:
        return _firebase_app

    # ── Option 1: Base64-encoded JSON from environment variable ──────────
    sa_b64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if sa_b64:
        try:
            sa_json = base64.b64decode(sa_b64).decode("utf-8")
            sa_dict = json.loads(sa_json)
            cred = credentials.Certificate(sa_dict)
            _firebase_app = firebase_admin.initialize_app(cred)
            print("[OK] Firebase Admin SDK initialized from environment variable.")
            return _firebase_app
        except Exception as e:
            print(f"[WARNING] Could not init Firebase from env var: {e}")

    # ── Option 2: Local JSON file ─────────────────────────────────────────
    sa_path = os.getenv(
        "FIREBASE_SERVICE_ACCOUNT_PATH",
        os.path.join(os.path.dirname(__file__), "firebase-service-account.json"),
    )
    if os.path.exists(sa_path):
        cred = credentials.Certificate(sa_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        print("[OK] Firebase Admin SDK initialized from file.")
        return _firebase_app

    print("[WARNING] Firebase service account not found. Auth verification will use unverified JWT decoding — for local dev only.")
    return None



def _decode_jwt_unverified(token):
    """Decode a JWT payload without verifying the signature.
    Used as fallback when Firebase Admin SDK is not configured.
    ONLY for local development — do not use in production without a service account.
    """
    try:
        # JWT is: header.payload.signature (base64url encoded)
        parts = token.split('.')
        if len(parts) != 3:
            return None
        # Add padding if necessary
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += '=' * padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_bytes)
        return payload
    except Exception:
        return None


def _verify_token(token):
    """Verify a Firebase ID token and return decoded claims."""
    if _firebase_app:
        # Production path: full verification
        try:
            decoded = firebase_auth.verify_id_token(token, check_revoked=True)
            return decoded
        except firebase_auth.RevokedIdTokenError:
            return None
        except firebase_auth.InvalidIdTokenError:
            return None
        except Exception:
            return None
    else:
        # Development fallback: decode without verification
        # Extracts uid/email from JWT payload without checking the signature
        payload = _decode_jwt_unverified(token)
        if payload and 'user_id' in payload:
            return {
                'uid': payload['user_id'],
                'email': payload.get('email', ''),
                'name': payload.get('name', '')
            }
        return None


def _extract_token():
    """Extract Bearer token from Authorization header."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


def require_auth(f):
    """Decorator: endpoint requires a valid Firebase auth token.
    Sets g.user_id and g.user_email on success.
    Returns 401 on failure.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if not token:
            return jsonify({"error": "Authentication required. Please sign in."}), 401

        claims = _verify_token(token)
        if not claims:
            return jsonify({"error": "Invalid or expired session. Please sign in again."}), 401

        g.user_id = claims['uid']
        g.user_email = claims.get('email', '')
        g.user_name = claims.get('name', '')
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    """Decorator: endpoint works with or without auth.
    If authenticated: sets g.user_id to the Firebase UID.
    If not authenticated: sets g.user_id to 'demo'.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_token()
        if token:
            claims = _verify_token(token)
            if claims:
                g.user_id = claims['uid']
                g.user_email = claims.get('email', '')
                g.user_name = claims.get('name', '')
            else:
                g.user_id = 'demo'
                g.user_email = ''
                g.user_name = ''
        else:
            g.user_id = 'demo'
            g.user_email = ''
            g.user_name = ''
        return f(*args, **kwargs)
    return decorated
