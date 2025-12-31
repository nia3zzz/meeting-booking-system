import zoneinfo
from django.db import models
from uuid import uuid4


def get_timezone_choices():
    return [(tz, tz) for tz in sorted(zoneinfo.available_timezones())]


# Create your models here.
# user model
class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    first_name = models.CharField(max_length=30)

    last_name = models.CharField(max_length=30)

    email = models.EmailField(unique=True)

    password = models.CharField(max_length=300)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email


class Timeslot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    from_time = models.DateTimeField()

    to_time = models.DateTimeField()

    timezone = models.CharField(
        max_length=65, choices=get_timezone_choices(), default="UTC"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.from_time} to {self.to_time}"


# booking model
class Booking(models.Model):
    # to be used as a enum class
    class TimeDurations(models.IntegerChoices):
        THIRTY_MIN = 30, "30 minutes"
        FORTY_FIVE_MIN = 45, "45 minutes"
        SIXTY_MIN = 60, "60 minutes"

    class MeetingPlatforms(models.TextChoices):
        ZOOM = "zoom", "Zoom"
        GOOGLE_MEET = "google meet", "Google meet"
        WHATSAPP_CALL = (
            "whatsapp call",
            "Whatsapp call",
        )
        MICROSOFT_TEAMS = "microsoft teams", "Microsoft teams"

    class BookingStatuses(models.TextChoices):
        REQUESTED = (
            "requested",
            "Requested",
        )
        CONFIRMED = (
            "confirmed",
            "Confirmed",
        )
        CANCELLED = (
            "cancelled",
            "Cancelled",
        )
        RESCHEDULED = (
            "rescheduled",
            "Rescheduled",
        )
        COMPLETED = ("completed", "Completed")

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    title = models.CharField(max_length=130)

    duration = models.SmallIntegerField(
        choices=TimeDurations.choices, default=TimeDurations.THIRTY_MIN
    )

    date = models.DateField()

    time_zone = models.CharField(
        max_length=65, choices=get_timezone_choices(), default="UTC"
    )

    time_suggestion_by_attendies = models.BooleanField(default=False)

    meeting_platform = models.CharField(
        max_length=50, choices=MeetingPlatforms.choices, default=MeetingPlatforms.ZOOM
    )

    attendes = models.ManyToManyField(
        User, through="Attendee", related_name="bookings"
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    timeslot = models.ForeignKey(
        Timeslot, on_delete=models.CASCADE
    )  # add timeslot model id

    status = models.CharField(
        max_length=50,
        choices=BookingStatuses.choices,
        default=BookingStatuses.REQUESTED,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} in {self.meeting_platform}"


# attendee junction
class Attendee(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="attendances")

    booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="booking_attendee"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "booking")

    def __str__(self):
        return f"{self.user.email} attendee in {self.booking.title}"


# timeslot suggestions table
class TimeslotSuggestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    user = models.ForeignKey(User, on_delete=models.CASCADE)

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE)

    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.user.email} suggested {self.timeslot.id} for {self.booking.title}"
        )


# rescheduled bookings table
class RescheduledBookings(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    prev_booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="rescheduled_from"
    )

    resc_booking = models.ForeignKey(
        Booking, on_delete=models.CASCADE, related_name="rescheduled_to"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.prev_booking.title} rescheduled."
