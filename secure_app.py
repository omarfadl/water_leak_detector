from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
from typing import Optional
from crud import DBUtils,User
from pydantic_extra_types.mac_address import MacAddress
from functools import wraps

app = FastAPI()

# Security settings
SECRET_KEY = "4200b2d5c7aed412b9c630b4e0f61521ac5504f51c6c3f1d30cbb64985e6d38d"  # Change this to a secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 14

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

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
    email: EmailStr = Field(
        ..., 
        description="This is the user email address", 
        examples=["user@gmail.com"]  # Use a list for examples
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
    email: Optional[str] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=14)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    # Fetch user data
    success, user = DBUtils.query_user_data(email=token_data.email)
    if not success or user is None:
        raise credentials_exception

    # Return only the user object, not the tuple
    return user

def user_ownership_required(endpoint):
    @wraps(endpoint)
    async def wrapper(*args, current_user: User  = Depends(get_current_user), **kwargs):
        # Check if the endpoint has an `email` parameter in args or kwargs
        email = kwargs.get("email") or kwargs.get("alert") and kwargs["alert"].email
        # Check if the endpoint has an `user_id` parameter in kwargs
        user_id = kwargs.get("user_id")
        if (email != current_user.email and email is not None) or (
            user_id!= current_user.id and user_id is not None):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to access this resource.",
            )
        
        return await endpoint(*args, current_user=current_user, **kwargs)
    return wrapper

# Token endpoint
@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    success,user = DBUtils.query_user_data(email=form_data.username)
    if not success or not verify_password(form_data.password, user.password_hashed):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email}, expires_delta=refresh_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

# Refresh token endpoint
@app.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    success,user = DBUtils.query_user_data(email=token_data.email)
    if not success:
        raise credentials_exception
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}

# Protected endpoints
@app.post("/alerts/")
@user_ownership_required
async def add_alert(alert: AddAlert, current_user: User = Depends(get_current_user)):
    # Check if the sensor belongs to the current user
    if not DBUtils.is_sensor_owned_by_user(email=current_user.email, sensor_mac_address=alert.sensor_mac_address):
        raise HTTPException(status_code=403, detail="You do not own this sensor.")
    success, message = DBUtils.add_alert(email=alert.email, sensor_mac_address=alert.sensor_mac_address, status=alert.status)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}

@app.post("/users")
def add_user(user: AddUserRequest):
    user.password_hashed = get_password_hash(user.password_hashed)
    success, message = DBUtils.add_user_only(user.name, user.email, user.password_hashed)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.get("/users/{email}/sensors")
@user_ownership_required
async def get_user_sensors(email: EmailStr, current_user: User = Depends(get_current_user)):
    success, message = DBUtils.query_user_and_sensors(email)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"sensors": message}

@app.get("/users/")
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

@app.get("/alerts/")
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

@app.post("/users/{email}/sensors")
@user_ownership_required
async def add_sensors(email: EmailStr, sensor: AddSensorRequest, current_user: User = Depends(get_current_user)):
    success, message = DBUtils.add_sensor_to_existing_user(email, sensor.sensor_name, sensor.mac_address)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message}

@app.delete("/users/{email}")
@user_ownership_required
def delete_user(email: str, current_user: User = Depends(get_current_user)):
    success, message = DBUtils.delete_user_and_cascade(email)
    if not success:
        raise HTTPException(status_code=404, detail=message)
    return {"message": message}

# Root endpoint
@app.get("/")
def root():
    return {"message": "User and Sensor Management API"}