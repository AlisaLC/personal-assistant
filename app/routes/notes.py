from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select
from datetime import datetime, UTC
from typing import List

from ..database import engine
from .. import models
from ..auth import get_current_user
from ..services.openai import (
    get_embedding,
    get_summary,
)


notes_router = APIRouter()

@notes_router.get("/api/notes/", response_model=List[models.NoteRead])
async def read_notes(current_user: models.User = Depends(get_current_user)):
    with Session(engine) as session:
        statement = select(models.Note).where(models.Note.user_id == current_user.id)
        notes = session.exec(statement).all()
        return notes
    
def update_note_embedding(note_id: int):
    with Session(engine) as session:
        statement = select(models.Note).where(models.Note.id == note_id)
        note = session.exec(statement).first()
        if note:
            note.embedding = get_embedding(note.text)
            note.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(note)

def update_note_summary(note_id: int):
    with Session(engine) as session:
        statement = select(models.Note).where(models.Note.id == note_id)
        note = session.exec(statement).first()
        if note:
            note.summary = get_summary(note.text)
            note.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(note)

@notes_router.post("/api/notes/", response_model=models.Note)
def create_note(note: models.NoteCreate, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user)):
    """Create a new note"""
    with Session(engine) as session:
        db_note = models.Note(
            text=note.text,
            user_id=current_user.id
        )
        session.add(db_note)
        session.commit()
        session.refresh(db_note)
        background_tasks.add_task(update_note_embedding, db_note.id)
        background_tasks.add_task(update_note_summary, db_note.id)
        return db_note
    
def get_note(session: Session, note_id: int, user_id: int):
    statement = select(models.Note).where(
        models.Note.id == note_id,
        models.Note.user_id == user_id
    )
    db_note = session.exec(statement).first()
    if not db_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return db_note

@notes_router.put("/api/notes/{note_id}", response_model=models.Note)
def update_note(note_id: int, note: models.NoteCreate, background_tasks: BackgroundTasks, current_user: models.User = Depends(get_current_user)):
    """Update a note"""
    with Session(engine) as session:
        db_note = get_note(session, note_id, current_user.id)
        db_note.text = note.text
        db_note.updated_at = datetime.now(UTC)
        session.commit()
        session.refresh(db_note)
        background_tasks.add_task(update_note_embedding, db_note.id)
        background_tasks.add_task(update_note_summary, db_note.id)
        return db_note

@notes_router.delete("/api/notes/{note_id}")
def delete_note(note_id: int, current_user: models.User = Depends(get_current_user)):
    """Delete a note"""
    with Session(engine) as session:
        db_note = get_note(session, note_id, current_user.id)
        session.delete(db_note)
        session.commit()
        return {"message": "Note deleted successfully"} 
