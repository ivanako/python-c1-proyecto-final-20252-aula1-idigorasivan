from datetime import datetime, timedelta, timezone

import jwt
import os

from flask import Blueprint, jsonify, request, current_app
from functools import wraps

from odontocare.admin.db_admin import User

bp_auth = Blueprint("auth", __name__, url_prefix="/auth/")

def jwt_required(roles=None):
    
    # if isinstance(roles, str):
    #     roles = [roles]
    
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            request_auth = request.headers.get("Authorization", "")

            if not request_auth.startswith("Bearer"):
                return jsonify({"error": "No Bearer token"}), 401

            jwt_token = request_auth.split(" ")[1]

            try:
                # jwt_payload = jwt.decode(jwt=jwt_token, key=os.getenv("JWT_KEY"), algorithms=[os.getenv("JWT_ALGORITHM")])
                jwt_payload = jwt.decode(jwt=jwt_token, key=current_app.config["JWT_SECRET_KEY"], algorithms=[os.getenv("JWT_ALGORITHM")])

                if roles is not None:
                    usr_role = jwt_payload.get("rol")

                    if not usr_role in roles:
                        return jsonify({"error": f"User with role '{usr_role}' not allowed to perform this action"}), 403

            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401

            # if roles is not None:
            #     if not jwt_payload.get("rol") in roles:
            #         return jsonify({"error": "User role not allowed"}), 403

            # Inject payload into the route
            return fn(jwt_payload, *args, **kwargs)

        return wrapper
    return decorator


@bp_auth.post("/login")
def login():
    data = request.get_json() or {}

    usr_username = data.get('usr_name')
    usr_pwd = data.get('usr_pwd')

    # Check if user exists
    usr_db = User.query.filter_by(usr_name=usr_username).first()

    if usr_db:
        if usr_db.usr_pwd != usr_pwd:
            return jsonify({'error': 'Wrong credentials'}), 401
    else:
        return jsonify({'error': 'User not found'}), 404
    
    usr_dict = usr_db.to_dict()

    # Build JWT payload
        # sub -> subject
        # rol -> role
        # iat -> issued at
        # exp -> expiration time
    payload = {
        "sub": str(usr_db.usr_id),
        "rol": usr_dict['usr_role'],
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30)
    }

    # jwt_token = jwt.encode(payload=payload, key=os.getenv("JWT_KEY"), algorithm=os.getenv("JWT_ALGORITHM"))
    jwt_token = jwt.encode(payload=payload, key=current_app.config["JWT_SECRET_KEY"], algorithm=os.getenv("JWT_ALGORITHM"))

    return jsonify({'access_token': jwt_token}), 200




@bp_auth.post("/add")
def add_user(payload):
    # payload contains: sub, rol, iat, exp
    if payload["rol"] != "admin":
        return jsonify({"error": "User role not allowed"}), 403

    data = request.get_json() or {}
    new_user = {
        "username": data.get("username"),
        "email": data.get("email")
    }

    return jsonify({"message": "User added", "user": new_user}), 201