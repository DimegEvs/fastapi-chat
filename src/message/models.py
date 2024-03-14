from datetime import datetime

from fastapi_users.db import BaseUserDatabase
from fastapi import Depends
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import (JSON, TIMESTAMP, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Table, func)

from src.database import Base

class Message(Base):
    __tablename__ = "message"
    id = Column(Integer, primary_key=True)
    message = Column(String, nullable= False)
    sender_id = Column(Integer, ForeignKey("user.id"))
    reciepient_id = Column(Integer, ForeignKey("user.id"))
    timestamp = Column(DateTime, default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.reciepient_id,
            'message': self.message,
            'timestamp': self.timestamp.isoformat() 
        }
        
    class Config:
        from_attributes = True
        