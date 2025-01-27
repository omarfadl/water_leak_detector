from fastapi import FastAPI
from app.routers import users,alerts,auth

app = FastAPI()

app.include_router(users.router)
app.include_router(alerts.router)
app.include_router(auth.router)


# Root endpoint
@app.get("/")
def root():
    return {"message": "User and Sensor Management API"}