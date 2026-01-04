from pydantic import BaseModel, Field, EmailStr, field_validator
from enum import IntEnum, Enum
import zoneinfo
import typing
from datetime import date


class MeetingDurationEnum(IntEnum):
    THIRTY_MIN = 30
    FORTY_FIVE_MIN = 45
    SIXTY_MIN = 60


class MeetingPlatformEnum(str, Enum):
    ZOOM = "zoom"
    GOOGLE_MEET = "google meet"
    WHATSAPP_CALL = "whatsapp call"
    MICROSOFT_TEAMS = "microsoft teams"


class RegisterUserValidator(BaseModel):
    first_name: str = Field(min_length=3, max_length=12)
    last_name: str = Field(min_length=3, max_length=12)
    email: EmailStr
    password: str = Field(min_length=6, max_length=30)


class LoginUserValidator(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=30)


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
