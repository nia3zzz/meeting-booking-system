from rest_framework.decorators import api_view
from rest_framework.response import Response
from app.pydantic import user_validators, booking_validators
from pydantic import ValidationError
from .models import User
from django.contrib.auth.hashers import make_password, check_password
import jwt
import os
from .serializers.user_serializer import UserSerializer
from .models import Booking, Timeslot, TimeslotSuggestion, Attendee
from app.auth.token_validator import validate_jwt
from datetime import datetime, time
from _zoneinfo import ZoneInfo
from .serializers.timeslot_serializer import TimeSlotSerializer
from .temp_emails.mail_funcs import attendee_mail, confirmed_meeting_mail


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


@api_view(["GET", "POST"])
def meeting_polls(request):
    # validate the user authentication
    user = validate_jwt(request)

    if not user:
        return Response(
            {
                "status": "error",
                "message": "Unauthorized.",
            },
            401,
        )

    # if the request is made on a get method fetch all the meetings of the user
    if request.method == "GET":
        # fetch all the bookings of the user
        bookings = Booking.objects.filter(
            user=user, status__in=["requested", "confirmed"]
        )

        # construct the response data
        data = []
        for booking in bookings:
            # fetch required data for each booking
            time_suggestions = TimeslotSuggestion.objects.filter(booking=booking)
            attendees = Attendee.objects.filter(booking=booking)

            # get all timeslot objects from the suggestions and serialize it
            suggested_timeslots = Timeslot.objects.filter(
                id__in=time_suggestions.values_list("timeslot_id", flat=True)
            )
            serialized_suggested_timeslots = TimeSlotSerializer(
                suggested_timeslots, many=True
            )

            # serialize attendees with details
            attendees_data = []
            for attendee in attendees:
                attendees_data.append(
                    {
                        "id": str(attendee.id),
                        "first_name": attendee.user.first_name,
                        "last_name": attendee.user.last_name,
                        "email": attendee.user.email,
                        "invited_at": attendee.created_at,
                    }
                )

            # serialize timeslot if exists
            timeslot_data = None
            if booking.timeslot:
                timeslot_data = TimeSlotSerializer(booking.timeslot).data

            data.append(
                {
                    "id": booking.id,
                    "title": booking.title,
                    "duration": booking.duration,
                    "date": booking.date if booking.date else None,
                    "time_zone": booking.time_zone,
                    "time_suggestion_by_attendies": serialized_suggested_timeslots.data,
                    "meeting_platform": booking.meeting_platform,
                    "attendes": attendees_data,
                    "timeslot": timeslot_data,
                    "status": booking.status,
                    "start_at": (booking.start_at if booking.start_at else None),
                    "end_at": (booking.end_at if booking.end_at else None),
                    "created_at": booking.created_at,
                    "updated_at": booking.updated_at,
                }
            )

        return Response(
            {
                "status": "success",
                "message": "Bookings fetched successfully.",
                "data": data,
            }
        )

    elif request.method == "POST":
        try:
            # validate the request body
            validated_data = booking_validators.CreateMeetingPollValidator(
                **request.data
            )
        except ValidationError as e:
            return Response(
                {
                    "status": "error",
                    "message": "Failed in type validation.",
                    "errors": [str(err) for err in e.errors()],
                },
                400,
            )

        # validate the time slots
        timeslot_objs = []
        for time_slot in validated_data.time_slot_ids:
            timeslot_obj = Timeslot.objects.filter(id=time_slot).first()
            if not timeslot_obj:
                return Response(
                    {
                        "status": "error",
                        "message": "Invalid time slot.",
                    },
                    400,
                )
            timeslot_objs.append(timeslot_obj)

        # check if a meeting is already confirmed on that day
        if Booking.objects.filter(
            date=validated_data.date, status="confirmed", timeslot__in=timeslot_objs
        ).exists():
            return Response(
                {
                    "status": "error",
                    "message": "A meeting is already booked on this date.",
                },
                400,
            )

        try:
            # create the booking
            create_booking = Booking(
                title=validated_data.title,
                duration=validated_data.duration,
                date=validated_data.date,
                time_zone=validated_data.time_zone,
                time_suggestion_by_attendies=validated_data.time_suggestion_by_attendies,
                meeting_platform=validated_data.meeting_platform,
                user=user,
            )

            create_booking.save()

            # save the attendees
            meeting_attendees = Attendee(user=user, booking=create_booking)
            meeting_attendees.save()

            # add the time slots to the time slot suggestion table
            for timeslot in timeslot_objs:
                booking_time_slot_suggestion = TimeslotSuggestion(
                    user=user,
                    booking=create_booking,
                    timeslot=timeslot,
                )

            booking_time_slot_suggestion.save()

            # count all the attendees
            attendees_number = Attendee.objects.filter(booking=create_booking).count()

            return Response(
                {
                    "status": "success",
                    "message": "Meeting booked successfully.",
                    "data": {
                        "id": create_booking.id,
                        "title": create_booking.title,
                        "duration": create_booking.duration,
                        "date": create_booking.date,
                        "time_zone": create_booking.time_zone,
                        "meeting_platform": create_booking.meeting_platform,
                        "attendees_number": attendees_number,
                        "status": create_booking.status,
                    },
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


@api_view(["GET"])
def get_timeslots(request):
    # validate the user authentication
    user = validate_jwt(request)

    if not user:
        return Response(
            {
                "status": "error",
                "message": "Unauthorized.",
            },
            401,
        )

    try:
        # validate the query
        validated_query = booking_validators.GetTimeslotsValidator(
            date=request.query_params.get("date"),
            time_zone=request.query_params.get("time_zone"),
        )
    except ValidationError as e:
        return Response(
            {
                "status": "error",
                "message": "Failed in query validation.",
                "errors": [str(err) for err in e.errors()],
            },
            400,
        )

    try:
        # time zone variable and custom type validation
        validated_time_zone = ZoneInfo(validated_query.time_zone)

        # start end of day in client timezone
        day_start_local = datetime.combine(validated_query.date, time.min).replace(
            tzinfo=validated_time_zone
        )
        day_end_local = datetime.combine(validated_query.date, time.max).replace(
            tzinfo=validated_time_zone
        )

        utc = ZoneInfo("UTC")

        # convert to UTC
        day_start_utc = day_start_local.astimezone(utc)
        day_end_utc = day_end_local.astimezone(utc)

        # fetch the time slots
        bookings = Booking.objects.filter(
            status="confirmed", start_at__gte=day_start_utc, end_at__lte=day_end_utc
        ).order_by("start_at")

        available_timeslots = Timeslot.objects.exclude(
            id__in=bookings.values_list("timeslot_id", flat=True)
        )

        # serialize and return the timeslots
        serialized_timeslots = TimeSlotSerializer(available_timeslots, many=True)

        return Response(
            {
                "status": "success",
                "message": "Time slots fetched successfully.",
                "data": serialized_timeslots.data,
            },
            200,
        )
    except Exception as e:
        return Response(
            {
                "status": "error",
                "message": "Something went wrong.",
            },
            500,
        )


@api_view(["POST"])
def invite_attendee(request):
    # validate the user authentication
    user = validate_jwt(request)

    if not user:
        return Response(
            {
                "status": "error",
                "message": "Unauthorized.",
            },
            401,
        )

    try:
        # validate the request data
        validated_data = booking_validators.InviteAttendeeValidator(**request.data)
    except ValidationError as e:
        return Response(
            {
                "status": "error",
                "message": "Failed in data validation.",
                "errors": e.errors(),
            },
            400,
        )

    # check if the booking exists
    found_booking = Booking.objects.filter(id=validated_data.booking_id).first()

    if not found_booking:
        return Response(
            {
                "status": "error",
                "message": "Booking not found.",
            },
            404,
        )

    # check if the user exists
    found_user = User.objects.filter(email=validated_data.attendee_email).first()

    if not found_user:
        return Response(
            {
                "status": "error",
                "message": "User not found.",
            },
            404,
        )

    # check if the booking is not completed
    if (
        found_booking.status == "completed"
        or found_booking.status == "cancelled"
        or found_booking.status == "rescheduled"
    ):
        return Response(
            {
                "status": "error",
                "message": "Cannot invite attendee to this meeting.",
            },
            400,
        )

    # check if the user is already an attendee
    if Attendee.objects.filter(user=found_user, booking=found_booking).exists():
        return Response(
            {
                "status": "error",
                "message": "User is already an attendee of this meeting.",
            },
            400,
        )

    try:

        # create the attendee
        attendee = Attendee(user=found_user, booking=found_booking)
        attendee.save()

        # send an email to the attendee user
        attendee_mail(
            user_firstname=found_user.first_name,
            meeting_title=found_booking.title,
            meeting_date=found_booking.date,
            meeting_time=found_booking.start_at,
            meeting_timezone=found_booking.time_zone,
            view_details_url=f"http://localhost:8000/meetings/{found_booking.id}/",
            attendee_email=found_user.email,
        )

        return Response(
            {
                "status": "success",
                "message": "Attendee invited successfully.",
                "data": {
                    "id": attendee.id,
                    "first_name": found_user.first_name,
                    "last_name": found_user.last_name,
                    "email": found_user.email,
                    "invited_at": attendee.created_at,
                },
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


@api_view(["GET"])
def get_attendees(request, booking_id):
    # validate the user authentication
    user = validate_jwt(request)

    if not user:
        return Response(
            {
                "status": "error",
                "message": "Unauthorized.",
            },
            401,
        )

    try:
        # validate the query params
        validated_query = booking_validators.GetAttendeesValidator(
            booking_id=booking_id,
        )
    except ValidationError as e:
        return Response(
            {
                "status": "error",
                "message": "Failed in type validation.",
                "errors": e.errors(),
            },
            400,
        )

    # check if the booking exists
    found_booking = Booking.objects.filter(id=validated_query.booking_id).first()

    if not found_booking:
        return Response(
            {
                "status": "error",
                "message": "Booking not found.",
            },
            404,
        )

    try:
        # fetch the attendees
        attendees = Attendee.objects.filter(booking=found_booking)

        attendees_data = []
        for attendee in attendees:
            attendee_data = {
                "id": attendee.id,
                "first_name": attendee.user.first_name,
                "last_name": attendee.user.last_name,
                "email": attendee.user.email,
                "invited_at": attendee.created_at,
            }
            attendees_data.append(attendee_data)

        return Response(
            {
                "status": "success",
                "message": "Attendees fetched successfully.",
                "data": attendees_data,
            },
            200,
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
def confirm_meeting_admin(request, booking_id):
    try:
        # validate the request data
        validated_data = booking_validators.ConfirmMeetingAdminValidator(
            booking_id=booking_id, timeslot_id=request.data.get("timeslot_id")
        )
    except ValidationError as e:
        return Response(
            {
                "status": "error",
                "message": "Failed in type validation.",
                "errors": e.errors(),
            },
            400,
        )

    # check if the booking exists
    found_booking = Booking.objects.filter(id=validated_data.booking_id).first()

    if not found_booking:
        return Response(
            {
                "status": "error",
                "message": "Booking not found.",
            },
            404,
        )

    # check if the booking is in requested status
    if found_booking.status != "requested":
        return Response(
            {
                "status": "error",
                "message": "Only requested meetings can be confirmed.",
            },
            400,
        )

    # check if the timeslot exists
    found_timeslot = Timeslot.objects.filter(id=validated_data.timeslot_id).first()

    if not found_timeslot:
        return Response(
            {
                "status": "error",
                "message": "Timeslot not found.",
            },
            404,
        )

    # check if the found time slot is among the meeting's suggested time slots
    if not TimeslotSuggestion.objects.filter(
        booking=found_booking, timeslot=found_timeslot
    ).exists():
        return Response(
            {
                "status": "error",
                "message": "Selected timeslot is not among suggested time slots for this meeting.",
            },
            400,
        )

    try:
        # build the start and end time
        local_tz = ZoneInfo(found_booking.time_zone)

        start_local = datetime.combine(
            found_booking.date, found_timeslot.from_time, tzinfo=local_tz
        )

        end_local = datetime.combine(
            found_booking.date, found_timeslot.to_time, tzinfo=local_tz
        )

        # confirm the meeting
        found_booking.timeslot = found_timeslot
        found_booking.status = "confirmed"
        found_booking.start_at = start_local.astimezone(ZoneInfo("UTC"))
        found_booking.end_at = end_local.astimezone(ZoneInfo("UTC"))
        found_booking.save()

        # send email to all attendees that the email has been confirmed
        attendees = Attendee.objects.filter(booking=found_booking)
        attendee_emails = [attendee.user.email for attendee in attendees]

        confirmed_meeting_mail(
            meeting_title=found_booking.title,
            meeting_date=found_booking.date,
            meeting_time=found_booking.start_at,
            meeting_timezone=found_booking.time_zone,
            meeting_duration=found_booking.duration,
            organizer_name=found_booking.user.first_name
            + " "
            + found_booking.user.last_name,
            organizer_email=found_booking.user.email,
            view_details_url=f"http://localhost:8000/meetings/{found_booking.id}/",
            attendee_emails=attendee_emails,
        )

        return Response(
            {
                "status": "success",
                "message": "Meeting confirmed successfully.",
            },
            200,
        )
    except Exception:
        return Response(
            {
                "status": "error",
                "message": "Something went wrong.",
            },
            500,
        )
