import jwt
import os
from meeting_booking_system.models import User

secret_key = os.getenv("JWT_SECRET")


# token validator for the validating jwt and returning user instance
def validate_jwt(request) -> User | None:
    token = request.COOKIES.get("access_cookie")

    if not token:
        return None

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return User.objects.filter(id=payload["user_id"]).first()

    except jwt.ExpiredSignatureError:
        return None

    except jwt.InvalidTokenError:
        return None
