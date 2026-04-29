import requests
import argparse
import sys
import time
import logging
from getpass import getpass
from typing import Optional

logger = logging.getLogger(__name__)

class CoreIotRpcController:
    def __init__(self, email: str, password: str, device_id: str):
        self.email = email
        self.password = password
        self.device_id = device_id
        self.base_url = "http://app.coreiot.io"
        self.token = None
        self.login()

    def login(self):
        """Login to CoreIoT and get JWT token"""
        url = f"{self.base_url}/api/auth/login"
        payload = {"username": self.email, "password": self.password}
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Login failed with status {response.status_code}: {response.text}")
            
            self.token = response.json().get("token")
            if not self.token:
                raise Exception("No token in response")
            
            logger.info("✓ Login successful")
        except Exception as e:
            logger.error("✗ Login error", exc_info=True)
            raise

    def send_rpc(self, method: str, params) -> dict:
        """Send RPC command to device"""
        if not self.token:
            print("Not logged in")
            return {}
        
        # Use twoway RPC for response
        url = f"{self.base_url}/api/rpc/twoway/{self.device_id}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"method": method, "params": params}
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✓ RPC sent: {method}({params}) -> {result}")
                return result
            else:
                logger.error(f"✗ RPC failed with status {response.status_code}: {response.text}")
                return {}
        except Exception as e:
            logger.error("✗ RPC error", exc_info=True)
            return {}

    def set_led(self, on: bool):
        """Send setLED02 RPC command"""
        return self.send_rpc("setLED02", on)

    def set_servo(self, angle: int):
        """Send setServo RPC command"""
        angle = max(0, min(180, int(angle)))
        return self.send_rpc("setServo", angle)

    def read_temp_humi(self) -> dict:
        """Read latest temperature and humidity telemetry from device"""
        if not self.token:
            print("Not logged in")
            return {}

        url = f"{self.base_url}/api/plugins/telemetry/DEVICE/{self.device_id}/values/timeseries"
        headers = {"Authorization": f"Bearer {self.token}"}
        params = {"keys": "temperature,humidity"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                logger.error(f"RPC telemetry read failed with status {response.status_code}: {response.text}")
                return {}

            raw = response.json()
            latest = {}
            for key in ("temperature", "humidity"):
                if key in raw and isinstance(raw[key], list) and raw[key]:
                    latest[key] = raw[key][0].get("value")

            if not latest:
                logger.info("No telemetry yet for temperature/humidity")
                return {}

            temp = latest.get("temperature", "N/A")
            humi = latest.get("humidity", "N/A")
            logger.info(f"Sensor -> temperature={temp}, humidity={humi}")
            return latest
        except Exception as e:
            logger.error("Telemetry read error", exc_info=True)
            return {}


def print_help():
    print("\nCommands:")
    print("  help                    Show this help")
    print("  led on                  Turn LED02 ON")
    print("  led off                 Turn LED02 OFF")
    print("  servo <0-180>           Set servo angle")
    print("  read                    Read latest temperature/humidity")
    print("  watch <seconds>         Poll temperature/humidity periodically")
    print("  exit                    Quit program\n")


def prompt_if_missing(value: Optional[str], label: str, secret: bool = False) -> str:
    if value:
        return value

    while True:
        entered = getpass(f"{label}: ") if secret else input(f"{label}: ")
        entered = entered.strip()
        if entered:
            return entered
        print(f"{label} is required")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="CoreIoT Server-side RPC Controller")
    parser.add_argument("--email", help="CoreIoT email")
    parser.add_argument("--password", help="CoreIoT password")
    parser.add_argument("--device-id", default="914ec000-24d4-11f1-8e7d-45cdb4e6c818", help="Target device ID (default: ESP32)")
    args = parser.parse_args()

    email = prompt_if_missing(args.email, "CoreIoT email")
    password = prompt_if_missing(args.password, "CoreIoT password", secret=True)
    device_id = args.device_id

    try:
        controller = CoreIotRpcController(email, password, device_id)
    except Exception as e:
        print(f"Failed to initialize controller: {e}")
        sys.exit(1)

    print_help()

    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue

            parts = cmd.split(" ", 1)
            head = parts[0].lower()

            if head == "help":
                print_help()
            elif head == "exit":
                break
            elif head == "led" and len(parts) >= 2:
                state = parts[1].lower()
                if state == "on":
                    controller.set_led(True)
                elif state == "off":
                    controller.set_led(False)
                else:
                    print("Use: led on | led off")
            elif head == "servo" and len(parts) >= 2:
                try:
                    angle = int(parts[1])
                    controller.set_servo(angle)
                except ValueError:
                    print("Servo angle must be a number")
            elif head == "read":
                controller.read_temp_humi()
            elif head == "watch" and len(parts) >= 2:
                try:
                    interval = float(parts[1])
                    if interval <= 0:
                        print("Interval must be > 0")
                        continue
                except ValueError:
                    print("Use: watch <seconds>")
                    continue

                print("Watching telemetry... Press Ctrl+C to stop")
                try:
                    while True:
                        controller.read_temp_humi()
                        time.sleep(interval)
                except KeyboardInterrupt:
                    print("Stopped watching")
            else:
                print("Unknown command. Type: help")

    except KeyboardInterrupt:
        print("\nInterrupted")


if __name__ == "__main__":
    main()
