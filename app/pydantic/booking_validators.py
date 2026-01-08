import zoneinfo
import typing
from datetime import date
from pydantic import BaseModel, Field, field_validator, EmailStr
from enum import IntEnum, Enum


class MeetingDurationEnum(IntEnum):
    THIRTY_MIN = 30
    FORTY_FIVE_MIN = 45
    SIXTY_MIN = 60


class MeetingPlatformEnum(str, Enum):
    ZOOM = "zoom"
    GOOGLE_MEET = "google meet"
    WHATSAPP_CALL = "whatsapp call"
    MICROSOFT_TEAMS = "microsoft teams"


class CreateMeetingPollValidator(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    duration: MeetingDurationEnum
    date: date
    time_zone: str = Field(default="UTC")
    time_slot_ids: typing.List[str]
    time_suggestion_by_attendies: bool = Field(default=False)
    meeting_platform: MeetingPlatformEnum

    @field_validator("time_zone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            zoneinfo.ZoneInfo(v)
        except Exception:
            raise ValueError("Invalid IANA timezone")
        return v


class GetTimeslotsValidator(BaseModel):
    date: date
    time_zone: str = Field(default="UTC")

    @field_validator("time_zone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            zoneinfo.ZoneInfo(v)
        except Exception:
            raise ValueError("Invalid IANA timezone")
        return v


class InviteAttendeeValidator(BaseModel):
    attendee_email: EmailStr
    booking_id: str = Field(min_length=32, max_length=36)


class GetAttendeesValidator(BaseModel):
    booking_id: str = Field(min_length=32, max_length=36)
