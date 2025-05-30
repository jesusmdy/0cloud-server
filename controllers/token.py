from datetime import datetime
import jwt
from flask import request, jsonify, g
from rdb.user import user_exists
from controllers.key import Key
from functools import wraps
from datetime import timedelta
from controllers.app import App
from controllers.session import SessionController


class TokenController:
    JWT_SECRET = Key.Load.jwt()
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION = timedelta(days=1)
    JWT_ISSUER = App.APP_NAME

    class Errors:
        SESSION_NOT_FOUND = "Session not found"
        USER_NOT_FOUND = "User not found"
        TOKEN_EXPIRED = "Token has expired"
        INVALID_TOKEN = "Invalid token"
        MISSING_TOKEN = "Missing token"

    def issue(
        user_id: str, email: str, display_name: str, private_key: str = None
    ) -> str:

        session = SessionController.create_session(user_id)
        if not session:
            return None

        payload = {
            "user_id": user_id,
            "email": email,
            "display_name": display_name,
            "exp": datetime.now() + TokenController.JWT_EXPIRATION,
            "iat": datetime.now(),
            "iss": TokenController.JWT_ISSUER,
            "session_id": session["id"],
        }
        if private_key:
            payload["private_key"] = private_key
        return jwt.encode(
            payload, TokenController.JWT_SECRET, algorithm=TokenController.JWT_ALGORITHM
        )

    def verify(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                TokenController.JWT_SECRET,
                algorithms=[TokenController.JWT_ALGORITHM],
                issuer=TokenController.JWT_ISSUER,
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise ValueError(TokenController.Errors.TOKEN_EXPIRED)
        except jwt.InvalidTokenError as e:
            raise ValueError(TokenController.Errors.INVALID_TOKEN)
        

    def require_jwt(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None

            auth_header = request.headers.get("Authorization")
            token = auth_header

            if not token:
                return jsonify({"error": TokenController.Errors.MISSING_TOKEN}), 401

            try:
                data = TokenController.verify(token)

                if not user_exists(data["user_id"]):
                    return (
                        jsonify({"error": TokenController.Errors.USER_NOT_FOUND}),
                        401,
                    )

                session = SessionController.get_session(
                    data["session_id"], data["user_id"]
                )
                if not session:
                    return (
                        jsonify({"error": TokenController.Errors.SESSION_NOT_FOUND}),
                        401,
                    )

                g.user = data
                return f(*args, **kwargs)

            except ValueError as e:
                return jsonify({"error": TokenController.Errors.INVALID_TOKEN}), 401

        return decorated_function
