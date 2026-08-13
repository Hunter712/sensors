import time
import requests
import logging
from adafruit_extended_bus import ExtendedI2C
import adafruit_bme680
import adafruit_bmp280
from adafruit_bme280.advanced import Adafruit_BME280_I2C

POLL_INTERVAL = 20.0
SERVER_URL = "http://192.168.31.96:8000/api/weather"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("sensor.log"),
        logging.StreamHandler()
    ]
)


def build_sensor_data(temp=None, press=None, hum=None, gas=None):
    """Categorizes sensor readings for telemetry payload."""
    data = {}

    if temp is not None:
        if temp < 20:
            data["temperature"] = [round(temp, 2), "cold"]
        elif temp <= 24:
            data["temperature"] = [round(temp, 2), "normal"]
        else:
            data["temperature"] = [round(temp, 2), "hot"]

    if press is not None:
        if press < 990:
            data["pressure"] = [round(press, 2), "low"]
        elif press <= 1005:
            data["pressure"] = [round(press, 2), "normal"]
        else:
            data["pressure"] = [round(press, 2), "high"]

    if hum is not None:
        if hum < 30:
            data["humidity"] = [round(hum, 2), "low"]
        elif hum <= 60:
            data["humidity"] = [round(hum, 2), "normal"]
        else:
            data["humidity"] = [round(hum, 2), "high"]

    if gas is not None:
        if gas < 20000:
            data["gas"] = [round(gas, 2), "bad"]
        elif gas < 50000:
            data["gas"] = [round(gas, 2), "satisfactory"]
        elif gas < 100000:
            data["gas"] = [round(gas, 2), "good"]
        else:
            data["gas"] = [round(gas, 2), "excellent"]

    return data


def send_data_to_server(payload):
    """Sends collected weather metrics to central server."""
    try:
        requests.post(SERVER_URL, json=payload, timeout=5.0)
        logging.info("Telemetry successfully delivered to server.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send data to server: {e}")


def initialize_sensors():
    """Initializes hardware devices on independent kernel virtual I2C buses."""
    sensors = {"bme680": None, "bmp280": None, "bme280": None}

    # BME680 on TCA9548A Channel 0 (/dev/i2c-11)
    try:
        i2c_ch0 = ExtendedI2C(11)
        sensors["bme680"] = adafruit_bme680.Adafruit_BME680_I2C(i2c_ch0)
        logging.info("BME680 initialized on bus /dev/i2c-11")
    except Exception as e:
        logging.error(f"Failed to initialize BME680 on ch0: {e}")

    # BMP280 on TCA9548A Channel 1 (/dev/i2c-12)
    try:
        i2c_ch1 = ExtendedI2C(12)
        sensors["bmp280"] = adafruit_bmp280.Adafruit_BMP280_I2C(i2c_ch1, address=0x76)
        logging.info("BMP280 initialized on bus /dev/i2c-12")
    except Exception as e:
        logging.error(f"Failed to initialize BMP280 on ch1: {e}")

    # BME280 on TCA9548A Channel 2 (/dev/i2c-13)
    try:
        i2c_ch2 = ExtendedI2C(13)
        sensors["bme280"] = Adafruit_BME280_I2C(i2c_ch2, address=0x76)
        logging.info("BME280 initialized on bus /dev/i2c-13")
    except Exception as e:
        logging.error(f"Failed to initialize BME280 on ch2: {e}")

    return sensors


def calculating_conditions():
    sensors = initialize_sensors()

    while True:
        sensors_data = {}
        t_list, p_list, h_list = [], [], []

        # Read BME680 (Ch0)
        if sensors["bme680"] is not None:
            try:
                t, p = sensors["bme680"].temperature, sensors["bme680"].pressure
                h, g = sensors["bme680"].humidity, sensors["bme680"].gas
                sensors_data["bme680"] = build_sensor_data(t, p, h, g)
                t_list.append(t)
                p_list.append(p)
                h_list.append(h)
            except Exception as e:
                sensors_data["bme680"] = {"error": str(e)}
                logging.error(f"[BME680 - Ch0] Read Error: {e}")

        # Read BMP280 (Ch1)
        if sensors["bmp280"] is not None:
            try:
                t, p = sensors["bmp280"].temperature, sensors["bmp280"].pressure
                sensors_data["bmp280"] = build_sensor_data(t, p)
                t_list.append(t)
                p_list.append(p)
            except Exception as e:
                sensors_data["bmp280"] = {"error": str(e)}
                logging.error(f"[BMP280 - Ch1] Read Error: {e}")

        # Read BME280 (Ch2)
        if sensors["bme280"] is not None:
            try:
                t, p, h = sensors["bme280"].temperature, sensors["bme280"].pressure, sensors["bme280"].humidity
                sensors_data["bme280"] = build_sensor_data(t, p, h)
                t_list.append(t)
                p_list.append(p)
                h_list.append(h)
            except Exception as e:
                sensors_data["bme280"] = {"error": str(e)}
                logging.error(f"[BME280 - Ch2] Read Error: {e}")

        # Calculate average telemetry metrics
        if t_list and p_list:
            avg_t = sum(t_list) / len(t_list)
            avg_p = sum(p_list) / len(p_list)
            avg_h = (sum(h_list) / len(h_list)) if h_list else None
            avg_g = sensors["bme680"].gas if sensors["bme680"] is not None else None
            sensors_data["AVG"] = build_sensor_data(avg_t, avg_p, avg_h, avg_g)
        else:
            sensors_data["AVG"] = {"error": "Sensors unavailable"}

        send_data_to_server(sensors_data)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    calculating_conditions()
