from crud import DBUtils

DBUtils.add_user_only(name="Esraa",email="estaa.attia.amany@gmail.com",password_hashed="lkjfdgoiure3445jtrt45trt")
DBUtils.add_user_only(name="Somaya",email="soma@gmail.com",password_hashed="lkjfdgoiure3445jtrt4543534dgtrt")

DBUtils.add_sensors_to_existing_user(
    user_email="estaa.attia.amany@gmail.com",
    sensors_data=[
        {"sensor_name": "Humidity Sensor", "mac_address": "66:77:88:99:AA:BB"},
        {"sensor_name": "Light Sensor", "mac_address": "CC:DD:EE:FF:00:11"}
                  ])

DBUtils.add_sensors_to_existing_user(
    user_email="estaa.attia.amany@gmail.com",
    sensors_data=[
        {"sensor_name": "Smoke Sensor", "mac_address": "66:A7:A8:99:AA:BB"},
        {"sensor_name": "Leak Sensor", "mac_address": "AC:DD:EE:FF:00:11"}
                  ])

