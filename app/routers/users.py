from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import EmailStr
from pydantic_extra_types.mac_address import MacAddress

from app.database.crud import DBUtils
from app.schemas.models import (
    AddUserRequest,
    AddSensorRequest
)
from app.database.models import User
from app.dependencies import get_current_user, user_ownership_required
from app.security import get_password_hash

router =APIRouter(prefix="/users", tags=["Users"])

@router.post("/")
def add_user(user: AddUserRequest):
    user.password_hashed = get_password_hash(user.password_hashed)
    success, message = DBUtils.add_user_only(user.name, user.email, user.password_hashed)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.get("/")
@user_ownership_required
async def get_user_data(
    email: EmailStr | None = Query(None, description="User's email address"),
    user_id: int | None = None,
    current_user: User = Depends(get_current_user)
):
    if user_id:
        success, message = DBUtils.query_user_data(user_id=user_id)
    elif email:
        success, message = DBUtils.query_user_data(email=email)
    else:
        raise HTTPException(status_code=400, detail="Either user email or user_id must be provided.")
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"data": message}

@router.get("/{email}/sensors")
@user_ownership_required
async def get_user_sensors(email: EmailStr, current_user: User = Depends(get_current_user)):
    success, message = DBUtils.query_user_and_sensors(email)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"sensors": message}

@router.post("/{email}/sensors")
@user_ownership_required
async def add_sensors(email: EmailStr, sensor: AddSensorRequest, current_user: User = Depends(get_current_user)):
    success, message = DBUtils.add_sensor_to_existing_user(email, sensor.sensor_name, sensor.mac_address)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@router.delete("/{email}")
@user_ownership_required
def delete_user(email: str, current_user: User = Depends(get_current_user)):
    success, message = DBUtils.delete_user_and_cascade(email)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}