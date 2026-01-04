# app/admin.py
from django.contrib import admin
from .models import (
    User,
    Timeslot,
    Booking,
    Attendee,
    TimeslotSuggestion,
    RescheduledBookings,
)

admin.site.register(User)
admin.site.register(Timeslot)
admin.site.register(Booking)
admin.site.register(Attendee)
admin.site.register(TimeslotSuggestion)
admin.site.register(RescheduledBookings)
