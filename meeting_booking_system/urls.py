from django.urls import path
from .views import (
    health,
    register_user,
    login_user,
    create_meeting_poll,
    get_timeslots,
    invite_attendee,
)

urlpatterns = [
    path("health/", health),
    path("auth/register/", register_user),
    path("auth/login/", login_user),
    path("meetings/", create_meeting_poll),
    path("timeslots/", get_timeslots),
    path("attendees/", invite_attendee),
]
