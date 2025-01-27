from pydantic import BaseModel,EmailStr,Field
from pydantic_extra_types.mac_address import MacAddress

# Pydantic models for request and response schemas
class AddUserRequest(BaseModel):
    name: str
    email: EmailStr = Field(
        ..., 
        description="This is the user email address", 
        examples=["user@gmail.com"]  
    )
    password_hashed: str = Field(..., min_length=8)

class AddAlert(BaseModel):
    email: EmailStr = Field(
        ..., 
        description="This is the user email address", 
        examples=["user@gmail.com"]  
    )
    status: bool = Field(description="True for Active alert , False for Resolved")
    sensor_mac_address: MacAddress = Field(
        ...,
        description="The MAC address of the sensor, in format XX:XX:XX:XX:XX:XX",
    )

class AddSensorRequest(BaseModel):
    sensor_name: str = Field(..., description="The name of the sensor", example="Temperature Sensor")
    mac_address: MacAddress = Field(
        ...,
        description="The MAC address of the sensor, in format XX:XX:XX:XX:XX:XX",
    )

class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class TokenData(BaseModel):
    email: str|None = None