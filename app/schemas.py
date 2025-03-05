from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime
from typing import Optional, List


class SensorDataBase(BaseModel):
    server_ulid: str = Field(..., description="Identificador único do servidor.")
    timestamp: datetime = Field(..., description="O timestamp dos dados de sensor.")
    temperature: Optional[float] = Field(None, description="Valor da temperatura.")
    humidity: Optional[float] = Field(None, description="Valor da umidade.")
    voltage: Optional[float] = Field(None, description="Valor da tensão.")
    current: Optional[float] = Field(None, description="Valor da corrente.")

    @field_validator("timestamp")
    def validate_timestamp(cls, value):
        if not value:
            raise ValueError("O timestamp é obrigatório.")
        return value

    @field_validator("server_ulid")
    def validate_server_ulid(cls, value):
        if not value:
            raise ValueError("O server_ulid é obrigatório.")
        return value

    @field_validator("temperature", "humidity", "voltage", "current", mode="before")
    def validate_sensor_value(cls, value):
        if isinstance(value, dict) and "value" in value:
            return value["value"] 
        return value

    @model_validator(mode='after')
    def validate_at_least_one_sensor(self):
        if not any(
            getattr(self, field) is not None
            for field in ["temperature", "humidity", "voltage", "current"]
        ):
            raise ValueError("Pelo menos um valor de sensor deve ser enviado.")
        return self

class SensorDataCreate(SensorDataBase):
    pass

class SensorData(SensorDataBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class SensorDataResponse(BaseModel):
    timestamp: datetime
    temperature: Optional[float]
    humidity: Optional[float]
    voltage: Optional[float]
    current: Optional[float]

    model_config = ConfigDict(from_attributes=True)

class AggregatedSensorDataResponse(BaseModel):
    timestamp: datetime
    temperature: Optional[float]
    humidity: Optional[float]
    voltage: Optional[float]
    current: Optional[float]

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ServerHealthResponse(BaseModel):
    server_ulid: str
    status: str
    server_name: str

class AllServersHealthResponse(BaseModel):
    servers: List[ServerHealthResponse]

class ServerCreate(BaseModel):
    server_name: str

class ServerResponse(BaseModel):
    server_ulid: str
    server_name: str
    created_at: datetime

    class Config:
        orm_mode = True