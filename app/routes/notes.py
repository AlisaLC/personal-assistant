from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
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
from ..services.search import search_service


notes_router = APIRouter()

NOTES_PER_PAGE = 15


@notes_router.get("/api/notes/", response_model=models.PaginatedResponse)
async def read_notes(
    page: int = Query(default=1, ge=1),
    current_user: models.User = Depends(get_current_user)
):
    with Session(engine) as session:
        count_statement = select(models.Note).where(models.Note.user_id == current_user.id)
        total_count = len(session.exec(count_statement).all())

        offset = (page - 1) * NOTES_PER_PAGE

        statement = select(models.Note).where(models.Note.user_id == current_user.id).offset(
            offset).limit(NOTES_PER_PAGE)
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
def create_note(
    note: models.NoteCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
):
    with Session(engine) as session:
        db_note = models.Note(
            text=note.text,
            user_id=current_user.id
        )
        session.add(db_note)
        session.commit()
        session.refresh(db_note)
        background_tasks.add_task(update_note_embedding, db_note.id)
        background_tasks.add_task(update_note_summary, db_note.id, note.text)
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
def update_note(
    note_id: int,
    note: models.NoteCreate,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
):
    with Session(engine) as session:
        db_note = get_note(session, note_id, current_user.id)
        db_note.text = note.text
        db_note.updated_at = datetime.now(UTC)
        session.commit()
        session.refresh(db_note)
        background_tasks.add_task(update_note_embedding, db_note.id)
        background_tasks.add_task(update_note_summary, db_note.id, note.text)
        return db_note


@notes_router.delete("/api/notes/{note_id}")
def delete_note(
    note_id: int,
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user),
):
    with Session(engine) as session:
        db_note = get_note(session, note_id, current_user.id)
        session.delete(db_note)
        session.commit()
        background_tasks.add_task(search_service.update_user_index, current_user.id)
        return {"message": "Note deleted successfully"}


@notes_router.get("/api/notes/search/", response_model=List[models.NoteRead])
async def search_notes(
    query: str = Query(...),
    min_results: int = Query(default=2, ge=1, le=10),
    max_results: int = Query(default=10, ge=1, le=50),
    min_similarity: float = Query(default=0.3, ge=0.0, le=1.0),
    current_user: models.User = Depends(get_current_user)
):
    query_embedding = get_embedding(query)

    try:
        note_ids = search_service.search(
            user_id=current_user.id,
            query_embedding=query_embedding,
            min_results=min_results,
            max_results=max_results,
            min_similarity=min_similarity
        )
    except ValueError as e:
        return []

    with Session(engine) as session:
        notes = []
        for note_id in note_ids:
            statement = select(models.Note).where(
                models.Note.id == note_id,
                models.Note.user_id == current_user.id
            )
            note = session.exec(statement).first()
            if note:
                notes.append(note)

        return notes
