
from datetime import datetime
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from sqlalchemy import TIMESTAMP, Boolean, Column, Integer, String, select

from src.database import Base, async_session_maker


class User(SQLAlchemyBaseUserTable[int], Base):
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    hashed_password: str = Column(String(length=1024), nullable=False)
    is_active: bool = Column(Boolean, default=True, nullable=False)
    is_superuser: bool = Column(Boolean, default=False, nullable=False)
    is_verified: bool = Column(Boolean, default=False, nullable=False)
    
    class Config:
        from_attributes = True
    
    
class UserService:
    
    @classmethod
    async def get_user(cls, user_id):
        async with async_session_maker() as session:
            query = select(User.name, User.surname).where(User.id == user_id)
            result = await session.execute(query)
            return result.mappings().all()