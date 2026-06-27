from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models import BookingStatus


class BookingBase(BaseModel):
    applicant_name: str
    machine_name: str
    purpose: str
    status: BookingStatus = BookingStatus.PENDING
    start_time: datetime
    end_time: datetime
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    usage_notes: str | None = None

    @field_validator("start_time", "end_time", "actual_start", "actual_end", mode="before")
    @classmethod
    def normalize_datetimes(cls, value: datetime | str | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    @field_validator("applicant_name", "machine_name", "purpose")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("end_time")
    @classmethod
    def validate_schedule_window(cls, value: datetime, info) -> datetime:
        start_time = info.data.get("start_time")
        if start_time and value <= start_time:
            raise ValueError("end_time must be later than start_time")
        return value

    @field_validator("actual_end")
    @classmethod
    def validate_actual_window(cls, value: datetime | None, info) -> datetime | None:
        actual_start = info.data.get("actual_start")
        if actual_start and value and value < actual_start:
            raise ValueError("actual_end must be later than or equal to actual_start")
        return value


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BookingBase):
    pass


class BookingRead(BookingBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarEvent(BaseModel):
    id: str
    title: str
    start: datetime
    end: datetime
    color: str
    extendedProps: dict
