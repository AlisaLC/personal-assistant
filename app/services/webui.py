from sqlmodel import Session, select
import uuid
from datetime import datetime

from ..database import webui_engine
from ..external_db.webui import WebUIAuth, WebUIUser
from ..auth import get_password_hash


async def create_webui_user(email: str, password: str, name: str) -> bool:
    with Session(webui_engine) as session:
        statement = select(WebUIAuth).where(WebUIAuth.email == email)
        if session.exec(statement).first():
            return False
        user_id = str(uuid.uuid4())
        password_hash = get_password_hash(password)
        session.add(
            WebUIAuth(
                id=user_id,
                email=email,
                password=password_hash
            )
        )
        session.add(
            WebUIUser(
                id=user_id,
                email=email,
                name=name,
                role="user",
                profile_image_url="/user.png",
                last_active_at=int(datetime.now().timestamp()),
                updated_at=int(datetime.now().timestamp()),
                created_at=int(datetime.now().timestamp())
            )
        )
        session.commit()
        return user_id
