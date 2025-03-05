from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from ulid import new
from app import models, schemas, auth

def create_sensor_data(db: Session, data: schemas.SensorDataCreate):
    db_data = models.SensorData(**data.dict())
    db.add(db_data)
    db.commit()
    db.refresh(db_data)
    return db_data

def get_sensor_data_by_server_ulid(db: Session, server_ulid: str):
    return db.query(models.SensorData).filter(models.SensorData.server_ulid == server_ulid).first()

def get_sensor_data(
    db: Session,
    server_ulid: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sensor_type: Optional[str] = None
):
    query = db.query(models.SensorData)

    if server_ulid:
        query = query.filter(models.SensorData.server_ulid == server_ulid)
    if start_time:
        query = query.filter(models.SensorData.timestamp >= start_time)
    if end_time:
        query = query.filter(models.SensorData.timestamp <= end_time)

    if sensor_type:
        if sensor_type == "temperature":
            query = query.filter(models.SensorData.temperature.isnot(None))
        elif sensor_type == "humidity":
            query = query.filter(models.SensorData.humidity.isnot(None))
        elif sensor_type == "voltage":
            query = query.filter(models.SensorData.voltage.isnot(None))
        elif sensor_type == "current":
            query = query.filter(models.SensorData.current.isnot(None))

    results = query.all()
    return results

def get_aggregated_sensor_data(
    db: Session,
    server_ulid: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    sensor_type: Optional[str] = None,
    aggregation: Optional[str] = None
):
    if aggregation not in ["minute", "hour", "day"]:
        raise ValueError("Aggregation deve ser 'minute', 'hour' ou 'day'.")
    
    if aggregation == "minute":
        time_trunc = func.date_trunc('minute', models.SensorData.timestamp)
    elif aggregation == "hour":
        time_trunc = func.date_trunc('hour', models.SensorData.timestamp)
    elif aggregation == "day":
        time_trunc = func.date_trunc('day', models.SensorData.timestamp)
    else:
        raise ValueError("Aggregation deve ser 'minute', 'hour' ou 'day'.")

    query = db.query(
        time_trunc.label("timestamp"),
        func.avg(models.SensorData.temperature).label("temperature"),
        func.avg(models.SensorData.humidity).label("humidity"),
        func.avg(models.SensorData.voltage).label("voltage"),
        func.avg(models.SensorData.current).label("current")
    )

    if server_ulid:
        query = query.filter(models.SensorData.server_ulid == server_ulid)
    if start_time:
        query = query.filter(models.SensorData.timestamp >= start_time)
    if end_time:
        query = query.filter(models.SensorData.timestamp <= end_time)

    if sensor_type:
        if sensor_type == "temperature":
            query = query.filter(models.SensorData.temperature.isnot(None))
        elif sensor_type == "humidity":
            query = query.filter(models.SensorData.humidity.isnot(None))
        elif sensor_type == "voltage":
            query = query.filter(models.SensorData.voltage.isnot(None))
        elif sensor_type == "current":
            query = query.filter(models.SensorData.current.isnot(None))

    query = query.group_by(time_trunc)
    results = query.all()
    return results

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_server(db: Session, server_name: str):
    server_ulid = str(new())
    created_at = datetime.utcnow()

    db_server = models.Server(
        server_ulid=server_ulid,
        server_name=server_name,
        created_at=created_at
    )
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    return db_server

def get_server_health(db: Session, server_ulid: str):
    last_data = (
        db.query(models.SensorData)
        .filter(models.SensorData.server_ulid == server_ulid)
        .order_by(models.SensorData.timestamp.desc())
        .first()
    )

    if not last_data:
        return None

    time_diff = datetime.utcnow() - last_data.timestamp
    status = "online" if time_diff.total_seconds() <= 10 else "offline"

    server = db.query(models.Server).filter(models.Server.server_ulid == server_ulid).first()

    return {
        "server_ulid": last_data.server_ulid,
        "status": status,
        "server_name": server.server_name
    }

def get_all_servers_health(db: Session):
    servers = (
        db.query(models.SensorData.server_ulid, models.SensorData.server_name)
        .distinct()
        .all()
    )

    results = []
    for server_ulid, server_name in servers:
        last_data = (
            db.query(models.SensorData)
            .filter(models.SensorData.server_ulid == server_ulid)
            .order_by(models.SensorData.timestamp.desc())
            .first()
        )

        if last_data:
            time_diff = datetime.utcnow() - last_data.timestamp
            status = "online" if time_diff.total_seconds() <= 10 else "offline"
            results.append({
                "server_ulid": server_ulid,
                "status": status,
                "server_name": server_name or "Unknown"
            })

    return results