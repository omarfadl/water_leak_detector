from sqlalchemy.orm import sessionmaker 
from model import User , engine, Sensor, Alert
from datetime import datetime
from typing import Tuple

Session= sessionmaker(engine)

class DBUtils():
    # Function to add a user without sensors
    @staticmethod
    def add_user_only(name:str, email:str, password_hashed:str)->Tuple[bool,str]:
        """
        Add a user without associating any sensors.

        :param name: The name of the user.
        :param email: The email of the user.
        :param password_hashed: The hashed password of the user.
        """
        with Session() as session:
            # Check if a user with the same email already exists
            existing_user = session.query(User).filter_by(email=email).first()
            if existing_user:
                print(f"User with email {email} already exists.")
                return (False,f"User already exists.")

            # Create and add the user
            new_user = User(name=name, email=email, password_hashed=password_hashed, total_sensors=0)
            session.add(new_user)
            session.commit()
            print(f"Added User: {new_user}")
            return (True,f"Added User: {new_user}")

    # Query a user and their sensors
    @staticmethod
    def query_user_and_sensors(user_email: str)->Tuple[bool,list]|Tuple[bool,str]:
        with Session() as session:
            user = session.query(User).filter_by(email=user_email).first()
            if user:
                print(f"Fetched User: {user}")
                print(f"Associated Sensors: {user.sensors}")
                return(True,user.sensors)
            else:
                print("User not found")
                return(False,"User not found")

    # Add sensor to an existing user
    @staticmethod
    def add_sensor_to_existing_user(user_email:str, sensor_name:str,mac_address:str)->Tuple[bool,str]:
        """
        Add sensors to an existing user.

        :param user_email: The email of the user to whom sensors should be added.
        :param sensors_name: name of the sensor like LeakSensor Sensorhumidity
        :param mac_address: sensor mac_address "AA:BB:CC:DD:EE:FF"
        """
        with Session() as session:
            # Query the user
            user = session.query(User).filter_by(email=user_email).first()
            if not user:
                print(f"User with email {user_email} not found.")
                return(False,f"User not found")
            # Add new sensors
            new_sensor = Sensor(sensor_name=sensor_name, mac_address=mac_address, user=user)
            session.add(new_sensor)
            
            # Update total sensors count
            user.total_sensors = len(user.sensors)
            
            # Commit the changes
            session.commit()
            print(f"Added sensors to user {user.name}: {user.sensors}")
            return(True,"Successfully Added sensors to user")

    # Delete a user and cascade delete their sensors
    @staticmethod
    def delete_user_and_cascade(user_email:str):
        with Session() as session:
            user_to_delete = session.query(User).filter_by(email=user_email).first()
            if user_to_delete:
                print(f"Deleting User: {user_to_delete}")
                session.delete(user_to_delete)
                session.commit()
                print("User and associated sensors deleted.")
                return(True,f"Successfully Deleted sensors&user Data")
            else:
                print("User not found for deletion.")
                return(False,f"User not found")

    # add Alert 
    @staticmethod
    def add_alert(email: str, sensor_mac_address: str, status: bool) -> Tuple[bool, str]:
        """
        Add a new alert for a user and sensor.

        :param email: The User Email .
        :param sensor_mac_address: The mac address of the sensor.
        :param status: The status of the alert (True for active, False for resolved).
        """
        with Session() as session:
            # Check if the user and sensor exist
            user = session.query(User).filter_by(email=email).first()
            sensor = session.query(Sensor).filter_by(mac_address=sensor_mac_address).first()

            if not user:
                return (False, "User not found.")
            if not sensor:
                return (False, "Sensor not found.")
            
            # Create and add the alert
            new_alert = Alert(
                user_id=user.id,
                sensor_id=sensor.id,
                status=status,
                date_time=datetime.utcnow()
            )
            session.add(new_alert)
            session.commit()
            return (True, f"Alert added successfully with ID {new_alert.id}.")
        
# DBUtils.add_alert(email="soma@gmail.com",sensor_mac_address="00:11:22:33:44:55",status=True)