import os
import time
import requests
import logging
import atexit
from adafruit_extended_bus import ExtendedI2C
import adafruit_bme680
import adafruit_bmp280
from adafruit_bme280.advanced import Adafruit_BME280_I2C

POLL_INTERVAL = float(os.getenv("POLL_INTERVAL", "20.0"))
SERVER_URL = os.getenv("SERVER_URL", "http://192.168.31.96:8000/api/weather")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)

http_session = requests.Session()

BUS_CONFIG = {
    "bme680": 11,
    "bmp280": 12,
    "bme280": 13,
}

I2C_BUSES = {}


def get_i2c_bus(name):
    if name not in I2C_BUSES:
        bus_id = BUS_CONFIG.get(name)
        if bus_id is None:
            return None
        try:
            I2C_BUSES[name] = ExtendedI2C(bus_id)
            logging.info(f"Opened persistent I2C bus /dev/i2c-{bus_id} for {name.upper()}")
        except Exception as e:
            logging.error(f"Failed to open I2C bus /dev/i2c-{bus_id} for {name.upper()}: {e}")
            return None
    return I2C_BUSES[name]


def cleanup_i2c_buses():
    for name, bus in list(I2C_BUSES.items()):
        try:
            bus.deinit()
            logging.info(f"Closed I2C bus for {name.upper()}")
        except Exception as e:
            logging.warning(f"Error closing I2C bus for {name.upper()}: {e}")
    I2C_BUSES.clear()

atexit.register(cleanup_i2c_buses)

def build_sensor_data(temp=None, press=None, hum=None, gas=None):
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
    try:
        response = http_session.post(SERVER_URL, json=payload, timeout=5.0)
        response.raise_for_status()
        logging.info("Telemetry successfully delivered to server.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send data to server: {e}")


def init_single_sensor(name):
    bus = get_i2c_bus(name)
    if bus is None:
        return None

    try:
        if name == "bme680":
            sensor = adafruit_bme680.Adafruit_BME680_I2C(bus)
            logging.info("BME680 initialized on bus /dev/i2c-11")
            return sensor
        if name == "bmp280":
            sensor = adafruit_bmp280.Adafruit_BMP280_I2C(bus, address=0x76)
            logging.info("BMP280 initialized on bus /dev/i2c-12")
            return sensor
        if name == "bme280":
            sensor = Adafruit_BME280_I2C(bus, address=0x76)
            logging.info("BME280 initialized on bus /dev/i2c-13")
            return sensor
    except Exception as e:
        logging.error(f"Failed to initialize {name.upper()}: {e}")
    return None


def calculating_conditions():
    sensors = {name: init_single_sensor(name) for name in ("bme680", "bmp280", "bme280")}

    while True:
        sensors_data = {}
        t_list, p_list, h_list = [], [], []
        latest_gas = None

        for name, instance in sensors.items():
            if instance is None:
                sensors[name] = init_single_sensor(name)

        if sensors["bme680"] is not None:
            try:
                t = sensors["bme680"].temperature
                p = sensors["bme680"].pressure
                h = sensors["bme680"].humidity
                g = sensors["bme680"].gas
                sensors_data["bme680"] = build_sensor_data(t, p, h, g)
                t_list.append(t)
                p_list.append(p)
                h_list.append(h)
                latest_gas = g
            except Exception as e:
                sensors_data["bme680"] = {"error": str(e)}
                sensors["bme680"] = None
                logging.error(f"[BME680 - Ch0] Read Error: {e}")

        if sensors["bmp280"] is not None:
            try:
                t = sensors["bmp280"].temperature
                p = sensors["bmp280"].pressure
                sensors_data["bmp280"] = build_sensor_data(t, p)
                t_list.append(t)
                p_list.append(p)
            except Exception as e:
                sensors_data["bmp280"] = {"error": str(e)}
                sensors["bmp280"] = None
                logging.error(f"[BMP280 - Ch1] Read Error: {e}")

        if sensors["bme280"] is not None:
            try:
                t = sensors["bme280"].temperature
                p = sensors["bme280"].pressure
                h = sensors["bme280"].humidity
                sensors_data["bme280"] = build_sensor_data(t, p, h)
                t_list.append(t)
                p_list.append(p)
                h_list.append(h)
            except Exception as e:
                sensors_data["bme280"] = {"error": str(e)}
                sensors["bme280"] = None
                logging.error(f"[BME280 - Ch2] Read Error: {e}")

        if t_list and p_list:
            avg_t = sum(t_list) / len(t_list)
            avg_p = sum(p_list) / len(p_list)
            avg_h = (sum(h_list) / len(h_list)) if h_list else None
            sensors_data["AVG"] = build_sensor_data(avg_t, avg_p, avg_h, latest_gas)
        else:
            sensors_data["AVG"] = {"error": "Sensors unavailable"}

        send_data_to_server(sensors_data)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    try:
        calculating_conditions()
    except KeyboardInterrupt:
        logging.info("Stopping telemetry collection (SIGINT)...")