from sqlalchemy import create_engine, ForeignKey, String
from sqlalchemy.orm import declarative_base, sessionmaker, Mapped, mapped_column, relationship

engine = create_engine(
    "mysql+pymysql://root:@127.0.0.1/esp32?charset=utf8mb4"
)
Session = sessionmaker(bind=engine)

Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100),nullable=False)
    password_hashed: Mapped[str] = mapped_column(String(200),nullable=False)
    email: Mapped[str] = mapped_column(String(100),nullable=False, unique=True)
    total_sensors: Mapped[int] = mapped_column(default=0, nullable=False)

    # One-to-Many Relationship
    sensors: Mapped[list["Sensor"]] = relationship("Sensor", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"User:(id={self.id}, name={self.name}, email={self.email})"


# Sensor model
class Sensor(Base):
    __tablename__ = "sensors"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sensor_name: Mapped[str] = mapped_column(String(100),nullable=True)
    mac_address: Mapped[str] = mapped_column(String(200),nullable=False)
    
    # Foreign Key to User
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Relationship back to User
    user: Mapped["User"] = relationship("User", back_populates="sensors")
    
    def __repr__(self)->str:
        return(f"Sensor_name: {self.sensor_name}, Senseor_Mac:{self.mac_address} , User_ID:{self.user_id}")

# Create tables
Base.metadata.create_all(engine)

