from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/rooms", tags=["rooms"])


@router.get("", response_model=list[schemas.RoomOut])
def list_rooms(floor: int | None = None, db: Session = Depends(get_db)):
    q = db.query(models.Room)
    if floor is not None:
        q = q.filter(models.Room.floor == floor)
    return q.order_by(models.Room.floor, models.Room.code).all()


@router.post("", response_model=schemas.RoomOut, status_code=201)
def create_room(payload: schemas.RoomCreate, db: Session = Depends(get_db)):
    if db.query(models.Room).filter(models.Room.code == payload.code).first():
        raise HTTPException(400, "Já existe uma sala com esse código.")
    room = models.Room(**payload.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.get("/{room_id}", response_model=schemas.RoomOut)
def get_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(404, "Sala não encontrada.")
    return room


@router.put("/{room_id}", response_model=schemas.RoomOut)
def update_room(room_id: int, payload: schemas.RoomCreate, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(404, "Sala não encontrada.")
    for k, v in payload.model_dump().items():
        setattr(room, k, v)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{room_id}", status_code=204)
def delete_room(room_id: int, db: Session = Depends(get_db)):
    room = db.get(models.Room, room_id)
    if not room:
        raise HTTPException(404, "Sala não encontrada.")
    db.delete(room)
    db.commit()
