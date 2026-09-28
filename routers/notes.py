from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from core.db import get_db
from repositories import notes as note_repository
from schemas.notes import NoteCreate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(note_data: NoteCreate, db: Session = Depends(get_db)):
	return note_repository.create_note(db, note_data)


@router.get("", response_model=list[NoteResponse])
def list_notes(db: Session = Depends(get_db)):
	return note_repository.list_notes(db)


@router.get("/{note_id}", response_model=NoteResponse)
def get_note(note_id: int, db: Session = Depends(get_db)):
	note = note_repository.get_note(db, note_id)
	if note is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
	return note


@router.put("/{note_id}", response_model=NoteResponse)
def update_note(note_id: int, note_data: NoteCreate, db: Session = Depends(get_db)):
	note = note_repository.get_note(db, note_id)
	if note is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
	return note_repository.update_note(db, note, note_data)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: int, db: Session = Depends(get_db)) -> Response:
	note = note_repository.get_note(db, note_id)
	if note is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
	note_repository.delete_note(db, note)
	return Response(status_code=status.HTTP_204_NO_CONTENT)
