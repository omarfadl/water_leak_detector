from sqlalchemy.orm import sessionmaker 
from model import User , engine, Sensor

Session= sessionmaker(engine)

class DBUtils():
    # Function to add a user without sensors
    @staticmethod
    def add_user_only(name:str, email:str, password_hashed:str):
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
                return

            # Create and add the user
            new_user = User(name=name, email=email, password_hashed=password_hashed, total_sensors=0)
            session.add(new_user)
            session.commit()
            print(f"Added User: {new_user}")

    # Query a user and their sensors
    @staticmethod
    def query_user_and_sensors(user_email: str):
        with Session() as session:
            user = session.query(User).filter_by(email=user_email).first()
            if user:
                print(f"Fetched User: {user}")
                print(f"Associated Sensors: {user.sensors}")
            else:
                print("User not found.")

    # Add sensors to an existing user
    @staticmethod
    def add_sensors_to_existing_user(user_email:str, sensors_data:dict[str,str]):
        """
        Add sensors to an existing user.

        :param user_email: The email of the user to whom sensors should be added.
        :param sensors_data: A list of dictionaries, where each dictionary contains sensor details.
                            Example: [{"sensor_name": "Sensor1", "mac_address": "00:11:22:33:44:55"}, ...]
        """
        with Session() as session:
            # Query the user
            user = session.query(User).filter_by(email=user_email).first()
            if not user:
                print(f"User with email {user_email} not found.")
                return
            
            # Add new sensors
            for sensor_info in sensors_data:
                new_sensor = Sensor(sensor_name=sensor_info["sensor_name"], mac_address=sensor_info["mac_address"], user=user)
                session.add(new_sensor)
            
            # Update total sensors count
            user.total_sensors = len(user.sensors)
            
            # Commit the changes
            session.commit()
            print(f"Added sensors to user {user.name}: {user.sensors}")

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
            else:
                print("User not found for deletion.")
