from sqlmodel import SQLModel, Field, Relationship, JSON
from datetime import datetime
from typing import Optional, List

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    first_name: str
    last_name: str
    birthdate: Optional[datetime] = None

class UserCreate(UserBase):
    password: str

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    notes: List["Note"] = Relationship(back_populates="user")

class UserRead(UserBase):
    id: int

class NoteBase(SQLModel):
    text: str
    summary: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Note(NoteBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    user: User = Relationship(back_populates="notes")
    embedding: Optional[List[float]] = Field(default=None, sa_type=JSON)

class NoteCreate(SQLModel):
    text: str

class NoteRead(NoteBase):
    id: int
    user_id: int
