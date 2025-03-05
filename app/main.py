from fastapi import FastAPI, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional, List
from app import models, schemas, crud, auth
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/auth/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.create_user(db=db, user=user)
    return db_user

@app.post("/auth/login", response_model=schemas.Token)
def login_for_access_token(user: schemas.UserCreate, db: Session = Depends(get_db)):
    authenticated_user = auth.authenticate_user(db, user.username, user.password)
    if not authenticated_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": authenticated_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/data", response_model=schemas.SensorData)
def create_sensor_data(
    data: schemas.SensorDataCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    existing_data = crud.get_sensor_data_by_server_ulid(db, server_ulid=data.server_ulid)
    if existing_data:
        raise HTTPException(
            status_code=400,
            detail="Já existem dados para este server_ulid."
        )
    
    if data.temperature is None and data.humidity is None and data.voltage is None and data.current is None:
        raise HTTPException(status_code=400, detail="Pelo menos um valor de sensor deve ser enviado.")
    return crud.create_sensor_data(db=db, data=data)

@app.get("/data", response_model=List[schemas.SensorDataResponse])
def get_sensor_data(
    server_ulid: Optional[str] = Query(None, description="Filtra por um servidor específico."),
    start_time: Optional[datetime] = Query(None, description="Início do intervalo de tempo."),
    end_time: Optional[datetime] = Query(None, description="Fim do intervalo de tempo."),
    sensor_type: Optional[str] = Query(None, description="Tipo de sensor (ex: temperature, humidity)."),
    aggregation: Optional[str] = Query(None, description="Granularidade da agregação (minute, hour, day)."),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    if aggregation:
        results = crud.get_aggregated_sensor_data(
            db=db,
            server_ulid=server_ulid,
            start_time=start_time,
            end_time=end_time,
            sensor_type=sensor_type,
            aggregation=aggregation
        )
        return [
            schemas.AggregatedSensorDataResponse(
                timestamp=row.timestamp,
                temperature=row.temperature,
                humidity=row.humidity,
                voltage=row.voltage,
                current=row.current
            )
            for row in results
        ]
    else:
        results = crud.get_sensor_data(
            db=db,
            server_ulid=server_ulid,
            start_time=start_time,
            end_time=end_time,
            sensor_type=sensor_type
        )
        return results

@app.post("/servers", response_model=schemas.ServerResponse)
def register_server(
    server: schemas.ServerCreate,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    db_server = crud.create_server(db, server_name=server.server_name)
    return db_server

@app.get("/health/{server_ulid}", response_model=schemas.ServerHealthResponse)
def get_server_health(
    server_ulid: str,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    server_health = crud.get_server_health(db, server_ulid=server_ulid)
    if not server_health:
        raise HTTPException(status_code=404, detail="Servidor não encontrado.")
    return server_health

@app.get("/healths/all", response_model=schemas.AllServersHealthResponse)
def get_all_servers_health(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(auth.get_current_user)
):
    servers_health = crud.get_all_servers_health(db)
    return {"servers": servers_health}