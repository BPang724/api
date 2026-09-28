from sqlalchemy import select
from sqlalchemy.orm import Session

from models.note import Note
from schemas.notes import NoteCreate


def create_note(db: Session, note_data: NoteCreate) -> Note:
	note = Note(**note_data.model_dump())
	db.add(note)
	db.commit()
	db.refresh(note)
	return note


def list_notes(db: Session) -> list[Note]:
	return list(db.scalars(select(Note).order_by(Note.id)).all())


def get_note(db: Session, note_id: int) -> Note | None:
	return db.get(Note, note_id)


def update_note(db: Session, note: Note, note_data: NoteCreate) -> Note:
	for field, value in note_data.model_dump().items():
		setattr(note, field, value)
	db.commit()
	db.refresh(note)
	return note


def delete_note(db: Session, note: Note) -> None:
	db.delete(note)
	db.commit()
