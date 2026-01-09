from django.urls import path
from .views import (
    health,
    register_user,
    login_user,
    meeting_polls,
    get_timeslots,
    invite_attendee,
    get_attendees,
)

urlpatterns = [
    path("health/", health),
    path("auth/register/", register_user),
    path("auth/login/", login_user),
    path("meetings/", meeting_polls),
    path("timeslots/", get_timeslots),
    path("attendees/", invite_attendee),
    path("attendees/<str:booking_id>/", get_attendees),
]
