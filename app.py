from crud import DBUtils
from fastapi import FastAPI, HTTPException,Query
from pydantic import BaseModel,Field,EmailStr
from pydantic_extra_types.mac_address import MacAddress


app = FastAPI()

# Pydantic models for request and response schemas
class AddUserRequest(BaseModel):
    name: str
    email: EmailStr = Field(
        ..., 
        description="This is the user email address", 
        examples=["user@gmail.com"]  # Use a list for examples
    )
    password_hashed: str

class AddAlert(BaseModel):
    user_email: EmailStr = Field(
        ..., 
        description="This is the user email address", 
        examples=["user@gmail.com"]  # Use a list for examples
    )
    status: bool = Field(description="True for Active alert , False for Resolved")
    sensor_mac_address: str = Field(
        ...,
        description="The MAC address of the sensor, in format XX:XX:XX:XX:XX:XX",
    )


class AddSensorRequest(BaseModel):
    sensor_name: str = Field(..., description="The name of the sensor", example="Temperature Sensor")
    mac_address: MacAddress = Field(
        ...,
        description="The MAC address of the sensor, in format XX:XX:XX:XX:XX:XX",
    )

# Submit alert data
@app.post("/alerts/")
async def add_alert(alert: AddAlert):
    success, message = DBUtils.add_alert(email=alert.user_email, sensor_mac_address=alert.sensor_mac_address, status=alert.status)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}

# Add a user without sensors
@app.post("/users")
def add_user(user: AddUserRequest):
    success, message = DBUtils.add_user_only(user.name, user.email, user.password_hashed)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

# Get user and their sensors
@app.get("/users/{email}/sensors")
async def get_user_sensors(email: str):
    success, message = DBUtils.query_user_and_sensors(email)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"sensors": message}


# Get user data
@app.get("/users/")
async def get_user_data(
    user_email: EmailStr | None = Query(None, description="User's email address"),
    user_id: int | None = None
):
    if user_id:
        success, message = DBUtils.query_user_data(user_id=user_id)
    elif user_email:
        success, message = DBUtils.query_user_data(user_email=user_email)
    else:
        raise HTTPException(status_code=400, detail="Either user_email or user_id must be provided.")
    
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"data": message}

# Add sensors to an existing user
@app.post("/users/{email}/sensors")
async def add_sensors(email: str, sensor: AddSensorRequest):

    success, message = DBUtils.add_sensor_to_existing_user(email, sensor.sensor_name,sensor.mac_address)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

# Delete a user and cascade delete their sensors
@app.delete("/users/{email}")
def delete_user(email: str):
    success, message = DBUtils.delete_user_and_cascade(email)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}

# Root endpoint
@app.get("/")
def root():
    return {"message": "User and Sensor Management API"}
