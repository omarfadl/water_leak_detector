from fastapi import HTTPException,APIRouter,Depends,Query
from app.dependencies import *
from pydantic import EmailStr
from app.database.crud import DBUtils
from app.database.models import User
from app.schemas.models import AddAlert

router= APIRouter(prefix="/alerts",tags=["Alerts"])

@router.get("/")
@user_ownership_required
async def get_user_alerts(
    email: EmailStr | None = Query(None, description="User's email address"),
    user_id: int | None = None,
    current_user: User = Depends(get_current_user)
):
    if user_id:
        success, message = DBUtils.query_user_alerts(user_id=user_id)
    elif email:
        success, message = DBUtils.query_user_alerts(email=email)
    else:
        raise HTTPException(status_code=400, detail="Either user email or user_id must be provided.")
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"alerts_data": message}

@router.post("/")
@user_ownership_required
async def add_alert(alert: AddAlert, current_user: User = Depends(get_current_user)):
    # Check if the sensor belongs to the current user
    if not DBUtils.is_sensor_owned_by_user(email=current_user.email, sensor_mac_address=alert.sensor_mac_address):
        raise HTTPException(status_code=403, detail="You do not own this sensor.")
    success, message = DBUtils.add_alert(email=alert.email, sensor_mac_address=alert.sensor_mac_address, status=alert.status)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}