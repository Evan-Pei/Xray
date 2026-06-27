from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Machine Usage Scheduler")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    today = date.today()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"default_year": today.year, "default_month": today.month},
    )


@app.get("/api/bookings", response_model=list[schemas.CalendarEvent])
def get_monthly_schedule(
    year: int = Query(..., ge=1900, le=3000),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
) -> list[schemas.CalendarEvent]:
    bookings = crud.list_bookings_for_month(db, year=year, month=month)
    return [schemas.CalendarEvent(**crud.serialize_calendar_event(booking)) for booking in bookings]


@app.get("/api/bookings/all", response_model=list[schemas.BookingRead])
def get_all_bookings(db: Session = Depends(get_db)) -> list[models.Booking]:
    return crud.list_all_bookings(db)


@app.get("/api/bookings/{booking_id}", response_model=schemas.BookingRead)
def get_booking(booking_id: int, db: Session = Depends(get_db)) -> models.Booking:
    try:
        return crud.get_booking(db, booking_id)
    except crud.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/api/bookings", response_model=schemas.BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(booking_in: schemas.BookingCreate, db: Session = Depends(get_db)) -> models.Booking:
    try:
        return crud.create_booking(db, booking_in)
    except crud.BookingConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.put("/api/bookings/{booking_id}", response_model=schemas.BookingRead)
def update_booking(
    booking_id: int, booking_in: schemas.BookingUpdate, db: Session = Depends(get_db)
) -> models.Booking:
    try:
        return crud.update_booking(db, booking_id, booking_in)
    except crud.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except crud.BookingConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@app.delete("/api/bookings/{booking_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_booking(booking_id: int, db: Session = Depends(get_db)) -> None:
    try:
        crud.delete_booking(db, booking_id)
    except crud.BookingNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
