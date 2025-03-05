from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from .database import Base
from datetime import datetime

class SensorData(Base):
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    server_ulid = Column(String, index=True) 
    server_name = Column(String, index=True)  
    timestamp = Column(DateTime)  
    temperature = Column(Float, nullable=True)  
    humidity = Column(Float, nullable=True) 
    voltage = Column(Float, nullable=True) 
    current = Column(Float, nullable=True)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    server_ulid = Column(String, unique=True, index=True)
    server_name = Column(String, index=True) 
    created_at = Column(DateTime, default=datetime.utcnow)  
