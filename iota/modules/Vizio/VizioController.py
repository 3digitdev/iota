import requests
import json
import os
import urllib3
from wakeonlan import send_magic_packet


# REFERENCE:  https://github.com/exiva/Vizio_SmartCast_API
class VizioController(object):
    def __init__(self):
        # Vizio's API is completely insecure, but it's also local only, so...
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        self.auth_token = os.environ['VIZIO_AUTH_TOKEN']
        self.ip = os.environ["VIZIO_IP_ADDRESS"]
        self.port = os.environ["VIZIO_PORT"]
        self.mac = os.environ["VIZIO_MAC_ADDRESS"]
        self.power_keys = {"off": 0, "on": 1, "toggle": 2}
        self.headers = {
            "Content-Type": "application/json",
            "AUTH": self.auth_token
        }

    def _build_url(self, parts: list) -> str:
        print(f"https://{self.ip}:{self.port}/{'/'.join(parts)}")
        return f"https://{self.ip}:{self.port}/{'/'.join(parts)}"

    def _call(self, method: str, parts: list, body={}) -> requests.Response:
        if method == "GET":
            response = requests.get(
                url=self._build_url(parts),
                headers=self.headers,
                verify=False
            )
        elif method == "PUT":
            response = requests.put(
                url=self._build_url(parts),
                headers=self.headers,
                data=json.dumps(body),
                verify=False
            )
        return response

    def _get_power_state(self) -> requests.Response:
        return self._call("GET", ["state", "device", "power_mode"])

    def _power_key(self, state: str) -> requests.Response:
        body = {
            "KEYLIST": [{
                "CODESET": 11,
                "CODE": self.power_keys[state],
                "ACTION": "KEYPRESS"
            }]
        }
        return self._call("PUT", ["key_command", ""], body)

    def turn_on(self):
        send_magic_packet(self.mac)
        self._power_key(state="on")

    def turn_off(self):
        self._power_key(state="off")

    def toggle_power(self):
        self._power_key(state="toggle")

    def _get_all_input_names(self) -> list:
        response = self._call(
            "GET",
            ["menu_native", "dynamic", "tv_settings", "devices", "name_input"]
        )
        if response.status_code == 200:
            return [item["NAME"] for item in response.json()["ITEMS"]]
        else:
            return []

    def _get_current_input(self) -> dict:
        response = self._call("GET", [
            "menu_native", "dynamic", "tv_settings", "devices", "current_input"
        ])
        if response.status_code == 200:
            input = response.json()["ITEMS"][0]
            return {"value": input["VALUE"], "hash": input["HASHVAL"]}
        else:
            return {}

    def switch_input(self, input_name: str) -> requests.Response:
        if input_name not in self._get_all_input_names():
            return None
        current = self._get_current_input()
        if "hash" not in current.keys():
            return None
        return self._call(
            method="PUT",
            parts=[
                "menu_native",
                "dynamic",
                "tv_settings",
                "devices",
                "current_input"
            ],
            body={
                "REQUEST": "MODIFY",
                "VALUE": input_name,
                "HASHVAL": current["hash"]
            }
        )


if __name__ == "__main__":
    print("wtf")
