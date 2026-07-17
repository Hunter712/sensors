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

def calculating_range(name, temp=None, press=None, hum=None, gas=None):
    temp_res = ""
    hum_res = ""
    press_res = ""
    gas_res = ""

    if temp is not None:
        temp_res = f"temperature: {temp:.2f} °C"

        if temp < 20:
            temp_res = temp_res + "(cold)"
        elif 20 <= temp <= 24:
            temp_res = temp_res + "(normal)"
        elif temp > 24:
            temp_res = temp_res + "(hot)"

    if hum is not None:
        hum_res = f"humidity: {hum:.2f} %"

        if hum < 30:
            hum_res = hum_res + "(low)"
        elif 30 <= hum <= 60:
            hum_res = hum_res + "(normal)"
        elif hum > 60:
            hum_res = hum_res + "(high)"

    if press is not None:
        press_res = f"pressure: {press:.2f} hPa"

        if press < 990:
            press_res = press_res + "(low)"
        elif 990 <= press <= 1005:
            press_res = press_res + "(normal)"
        elif press > 1005:
            press_res = press_res + "(high)"


    if gas is not None:
        gas_res = f"gas: {gas:.2f} Ohms"

        if gas < 12000:
            gas_res = gas_res + "(bad)"
        elif 12000 <= gas <= 30000:
            gas_res = gas_res + "(satisfactory)"
        elif 30000 <= gas <= 60000:
            gas_res = gas_res + "(good)"
        elif gas > 60000:
            gas_res = gas_res + "(excellent)"

    return f"{name}: {temp_res} {press_res} {hum_res} {gas_res}"


def send_data_to_server(data):
    try:
        headers = {'Content-Type': 'text/plain; charset=utf-8'}
        requests.post(SERVER_URL, data=data.encode('utf-8'), headers=headers, timeout=5.0)
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send data to server: {e}")

def calculating_conditions():
    final_data = ""

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
                final_data = calculating_range('bme680', bme680.temperature, bme680.pressure, bme680.humidity, bme680.gas)
            except Exception as e:
                final_data = f"[BME680 - Ch0] Error reading data: {e}"
                logging.error(final_data)
        else:
            final_data = "[BME680 - Ch0] Sensor not available"

        if bme280 is not None:
            try:
                final_data += f"\n{calculating_range('bme280', bme280.temperature, bme280.pressure, bme280.humidity)}"
            except Exception as e:
                final_data += f"\n[BME280 - Ch2] Error reading data: {e}"
                logging.error(final_data)
        else:
            final_data += "\n[BME280 - Ch2] Sensor not available"

        if bmp280 is not None:
            try:
                final_data += f"\n{calculating_range('bmp280', bmp280.temperature, bmp280.pressure)}"
            except Exception as e:
                final_data += f"\n[BMP280 - Ch1] Error reading data: {e}"
                logging.error(final_data)
        else:
            final_data += "\n[BMP280 - Ch1] Sensor not available"

        send_data_to_server(final_data)
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    calculating_conditions()
