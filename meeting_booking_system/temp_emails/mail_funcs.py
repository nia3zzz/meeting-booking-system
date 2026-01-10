from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings


def attendee_mail(
    user_firstname,
    meeting_title,
    meeting_date,
    meeting_time,
    meeting_timezone,
    view_details_url,
    attendee_email,
):
    try:
        # html content for the email
        html_content = render_to_string(
            "attendee_temp.html",
            context={
                "user_firstname": user_firstname,
                "meeting_title": meeting_title,
                "meeting_date": meeting_date,
                "meeting_time": meeting_time,
                "meeting_timezone": meeting_timezone,
                "view_details_url": view_details_url,
            },
        )

        # email object instance
        msg = EmailMultiAlternatives(
            subject="You're Invited to a Meeting.",
            body="You're invited to a meeting.",
            from_email=settings.EMAIL_HOST_USER,
            to=[attendee_email],
        )

        # attach the html content
        msg.attach_alternative(html_content, "text/html")

        # send the email
        msg.send()
    except Exception as e:
        print(f"Error sending attendee email: {e}")


def confirmed_meeting_mail(
    meeting_title,
    meeting_date,
    meeting_time,
    meeting_timezone,
    meeting_duration,
    organizer_name,
    organizer_email,
    view_details_url,
    attendee_emails,
):
    try:
        # html content for the email
        html_content = render_to_string(
            "confirmed_meeting_temp.html",
            context={
                "meeting_title": meeting_title,
                "meeting_date": meeting_date,
                "meeting_time": meeting_time,
                "meeting_timezone": meeting_timezone,
                "meeting_duration": meeting_duration,
                "organizer_name": organizer_name,
                "organizer_email": organizer_email,
                "view_details_url": view_details_url,
            },
        )

        # email object instance
        msg = EmailMultiAlternatives(
            subject="Meeting Confirmed.",
            body="Your meeting has been confirmed.",
            from_email=settings.EMAIL_HOST_USER,
            to=attendee_emails,
        )

        # attach the html content
        msg.attach_alternative(html_content, "text/html")

        # send the email
        msg.send()
    except Exception as e:
        print(f"Error sending confirmed meeting email: {e}")
