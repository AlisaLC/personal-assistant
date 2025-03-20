from sqlmodel import SQLModel, Field
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base


WebUIBase = declarative_base()

class WebUIAuth(WebUIBase, SQLModel, table=True):
    __tablename__ = "auth"
    
    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    password: str
    active: bool = Field(default=True)


class WebUIUser(WebUIBase, SQLModel, table=True):
    __tablename__ = "user"
    
    id: str = Field(primary_key=True)
    name: str
    email: str = Field(unique=True, index=True)
    role: str
    profile_image_url: str
    oauth_sub: str
    last_active_at: int
    updated_at: int
    created_at: int 