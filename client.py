import time
import board
import adafruit_tca9548a
import adafruit_bme680
import adafruit_bmp280
from adafruit_bme280.advanced import Adafruit_BME280_I2C
import requests
import logging

POLL_INTERVAL = 10.0
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
    data = {}

    if temp is not None:
        if temp < 20:
            data["temperature"] = [round(temp, 2), "cold"]
        elif 20 <= temp <= 24:
            data["temperature"] = [round(temp, 2), "normal"]
        elif temp > 24:
            data["temperature"] = [round(temp, 2), "hot"]

    if press is not None:
        data["pressure"] = round(press, 2)

        if press < 990:
            data["pressure"] = [round(press, 2), "low"]
        elif 990 <= press <= 1005:
            data["pressure"] = [round(press, 2), "normal"]
        elif press > 1005:
            data["pressure"] = [round(press, 2), "high"]

    if hum is not None:
        data["humidity"] = round(hum, 2)

        if hum < 30:
            data["humidity"] = [round(hum, 2), "low"]
        elif 30 <= hum <= 60:
            data["humidity"] = [round(hum, 2), "normal"]
        elif hum > 60:
            data["humidity"] = [round(hum, 2), "high"]

    if gas is not None:
        if gas < 12000:
            data["gas_rating"] = "bad"
            data["gas"] = [round(gas, 2), "bad"]
        elif 12000 <= gas <= 30000:
            data["gas"] = [round(gas, 2), "satisfactory"]
        elif 30000 <= gas <= 60000:
            data["gas"] = [round(gas, 2), "good"]
        elif gas > 60000:
            data["gas"] = [round(gas, 2), "excellent"]

    return data


def send_data_to_server(payload):
    try:
        requests.post(SERVER_URL, json=payload, timeout=5.0)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send data to server: {e}")

def calculating_conditions():
    sensors_data = {}

    try:
        i2c = board.I2C()
    except Exception as e:
        logging.error(f"Failed to initialize I2C: {e}")
        return

    try:
        tca = adafruit_tca9548a.TCA9548A(i2c)
    except Exception as e:
        logging.error(f"Failed to initialize PCA9548A: {e}")
        return

    try:
        bme680 = adafruit_bme680.Adafruit_BME680_I2C(tca[0])
    except Exception as e:
        bme680 = None
        logging.error(f"Failed to initialize bme680: {e}")

    try:
        bmp280 = adafruit_bmp280.Adafruit_BMP280_I2C(tca[1], address=0x76)
    except Exception as e:
        bmp280 = None
        logging.error(f"Failed to initialize bmp280: {e}")

    try:
        bme280 = Adafruit_BME280_I2C(tca[2], address=0x76)
    except Exception as e:
        bme280 = None
        logging.error(f"Failed to initialize bme280 on ch2: {e}")

    while True:

        if bme680 is not None:
            try:
                sensors_data["bme680"] = build_sensor_data(bme680.temperature, bme680.pressure, bme680.humidity, bme680.gas)
            except Exception as e:
                sensors_data["bme680"] = {"error": str(e)}
                logging.error(f"[BME680 - Ch0] Error: {e}")
        else:
            sensors_data["bme680"] = {"error": "Sensor not available"}

        if bme280 is not None:
            try:
                sensors_data["bme280"] = build_sensor_data(bme280.temperature, bme280.pressure, bme280.humidity)
            except Exception as e:
                sensors_data["bme280"] = {"error": str(e)}
                logging.error(f"[BME280 - Ch0] Error: {e}")
        else:
            sensors_data["bme280"] = {"error": "Sensor not available"}

        if bmp280 is not None:
            try:
                sensors_data["bmp280"] = build_sensor_data(bmp280.temperature, bmp280.pressure)
            except Exception as e:
                sensors_data["bmp280"] = {"error": str(e)}
                logging.error(f"[BMP280 - Ch0] Error: {e}")
        else:
            sensors_data["bmp280"] = {"error": "Sensor not available"}

        send_data_to_server(sensors_data)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    calculating_conditions()
