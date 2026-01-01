from rest_framework.decorators import api_view
from rest_framework.response import Response
from app.pydantic import user_validators
from pydantic import ValidationError
from .models import User
from django.contrib.auth.hashers import make_password, check_password
import jwt
import os
from .serializers.user_serializer import UserSerializer


@api_view(["GET"])
def health(request):
    return Response(
        {
            "status": "success",
            "message": "APIs are running.",
        },
        200,
    )


@api_view(["POST"])
def register_user(request):
    try:
        # validate the request body
        validated_data = user_validators.RegisterUserValidator(**request.data)
    except ValidationError as e:
        return Response(
            {
                "status": "error",
                "message": "Failed in type validation.",
                "errors": e.errors(),
            },
            400,
        )

    # check user with provided email already exists
    if User.objects.filter(email=validated_data.email).exists():
        return Response(
            {
                "status": "error",
                "message": "User already exists with this email.",
            },
            409,
        )

    try:
        # hash the password
        hashed_password = make_password(
            validated_data.password, salt=None, hasher="default"
        )

        # create the user
        user = User(
            first_name=validated_data.first_name,
            last_name=validated_data.last_name,
            email=validated_data.email,
            password=hashed_password,
        )

        user.save()

        return Response(
            {
                "status": "success",
                "message": "User registered successfully.",
                "data": {"id": user.id},
            },
            201,
        )
    except Exception:
        return Response(
            {
                "status": "error",
                "message": "Something went wrong.",
            },
            500,
        )


@api_view(["POST"])
def login_user(request):
    try:
        # validate the request body
        validated_data = user_validators.LoginUserValidator(**request.data)
    except ValidationError as e:
        return Response(
            {
                "status": "error",
                "message": "Failed in type validation.",
                "errors": e.errors(),
            },
            400,
        )

    # check if a user exists with this email
    found_user = User.objects.filter(email=validated_data.email).first()

    if not found_user:
        return Response({"status": "error", "message": "Invalid credentials."}, 401)

    # check the password
    verify_password = check_password(
        validated_data.password, found_user.password, setter=None, preferred="default"
    )

    if not verify_password:
        return Response({"status": "error", "message": "Invalid credentials."}, 401)

    try:
        # serialize the user document
        serialized_user = UserSerializer(found_user, many=False)

        # build a jwt
        jwt_secret = os.getenv("JWT_SECRET")

        jwt_hash = jwt.encode(
            {"user_id": serialized_user.data["id"]}, jwt_secret, algorithm="HS256"  # type: ignore
        )

        # return to client
        response = Response(
            {"status": "success", "message": "User logged in successfully."}, 200
        )
        response.set_cookie(
            "access_cookie", jwt_hash, max_age=3600 * 24 * 30, httponly=True
        )
        return response

    except Exception as e:
        return Response({"status": "error", "message": "Something went wrong."}, 500)
