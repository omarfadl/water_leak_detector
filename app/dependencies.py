from functools import wraps
from fastapi import HTTPException,status,Depends
from jose import JWTError, jwt
from app.schemas.models import TokenData
from app.security import oauth2_scheme, SECRET_KEY, ALGORITHM
from app.database.models import User
from app.database.crud import DBUtils

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