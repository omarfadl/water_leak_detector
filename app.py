from crud import DBUtils
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel,Field,EmailStr

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
    staus: bool = Field(description="True for Active alert , False for Resolved")
    sensor_mac_address: str = Field(
        ...,
        description="The MAC address of the sensor, in format XX:XX:XX:XX:XX:XX",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", 
        example=["00:11:22:33:44:55"]
    )


class AddSensorRequest(BaseModel):
    sensor_name: str = Field(..., description="The name of the sensor", example="Temperature Sensor")
    mac_address: str = Field(
        ...,
        description="The MAC address of the sensor, in format XX:XX:XX:XX:XX:XX",
        pattern=r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$", 
        example=["00:11:22:33:44:55"]
    )

@app.post("/add_alert/")
async def add_alert(alert: AddAlert):
    success, message = DBUtils.add_alert(email=alert.user_email, sensor_mac_address=alert.sensor_mac_address, status=alert.staus)
    if not success:
        raise HTTPException(status_code=400, detail=message)
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
    success, data = DBUtils.query_user_and_sensors(email)
    if not success:
        raise HTTPException(status_code=404, detail=data)
    return {"sensors": data}

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
