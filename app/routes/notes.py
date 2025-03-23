from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from sqlmodel import Session, select
from datetime import datetime, UTC
from typing import List, Optional

from ..database import engine
from .. import models
from ..auth import get_current_user
from ..services.openai import (
    get_embedding,
    get_summary,
)
from ..services.search import search_service


notes_router = APIRouter()

NOTES_PER_PAGE = 15  # Fixed number of notes per page

@notes_router.get("/api/notes/", response_model=models.PaginatedResponse)
async def read_notes(
    page: int = Query(default=1, ge=1),
    current_user: models.User = Depends(get_current_user)
):
    with Session(engine) as session:
        # Get total count
        count_statement = select(models.Note).where(models.Note.user_id == current_user.id)
        total_count = len(session.exec(count_statement).all())
        
        # Calculate offset from page number
        offset = (page - 1) * NOTES_PER_PAGE
        
        # Get paginated notes
        statement = select(models.Note).where(models.Note.user_id == current_user.id).offset(offset).limit(NOTES_PER_PAGE)
        notes = session.exec(statement).all()
        
        return {
            "notes": notes,
            "total": total_count,
            "page": page,
            "total_pages": (total_count + NOTES_PER_PAGE - 1) // NOTES_PER_PAGE
        }
    
def update_note_embedding(note_id: int):
    with Session(engine) as session:
        statement = select(models.Note).where(models.Note.id == note_id)
        note = session.exec(statement).first()
        if note:
            note.embedding = get_embedding(note.text)
            note.updated_at = datetime.now(UTC)
            session.commit()
            session.refresh(note)
    
    search_service.update_user_index(note.user_id)

def update_note_summary(note_id: int, note_text: str):
    summary = get_summary(note_text)

    with Session(engine) as session:
        statement = select(models.Note).where(models.Note.id == note_id)
        note = session.exec(statement).first()
        if note:
            note.summary = summary
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
