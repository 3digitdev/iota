import requests
import time
import json


class HueController(object):
    def __init__(self):
        self.user = "7wl8U1CnKZlk6kE8WHPzCQatw5VqWb0oiqjZFinR"
        self.api_base = f"http://192.168.1.4/api/{self.user}"
        self.group_map = {}
        self.light_map = {}
        self.group_aliases = {
            'Lamp': [
                'living room',
                'livingroom',
                'lamp'
            ],
            'Bedroom': [
                'bed room',
                'bedroom',
                'master bedroom',
                'master bed room'
            ],
            'Craft Room': [
                'office',
                'craftroom',
                'craft room'
            ]
        }
        self._init_states()

    def _init_states(self):
        groups = self.get_groups()
        if groups.status_code != 200:
            print(f"Cannot reach Hue bridge at {self._build_url(['groups'])}")
            exit(1)
        for id, group in groups.json().items():
            self.group_map[group["name"]] = id
        lights = self.get_lights()
        if lights.status_code != 200:
            print(f"Cannot reach Hue bridge at {self._build_url(['lights'])}")
            exit(1)
        for id, light in lights.json().items():
            self.light_map[light["name"]] = id

    def _build_url(self, parts: list) -> str:
        return "/".join([self.api_base, *parts])

    def _clamp_brightness(self, bright: int) -> int:
        return max(0, min(int(254 * (bright / 100)), 254))

    def get_lights(self) -> requests.Response:
        return requests.get(
            url=self._build_url(["lights"])
        )

    def _get_light_id(self, name: str) -> str:
        if name not in self.light_map.keys():
            print(f"ERROR:  Cannot find Light named {name}")
            exit(1)
        return str(self.light_map[name])

    def get_light_by_name(self, name: str) -> requests.Response:
        return requests.get(
            url=self._build_url(["lights", self._get_light_id(name)])
        )

    def turn_on_light(self, id: str, bright: int = None) -> requests.Response:
        body = {"on": True}
        if bright is not None:
            body["bri": self._clamp_brightness(bright)]
        return requests.put(
            url=self._build_url(["lights", id, "state"]),
            data=json.dumps(body)
        )

    def turn_off_light(self, id: str) -> requests.Response:
        return requests.put(
            url=self._build_url(["lights", id, "state"]),
            data=json.dumps({"on": False})
        )

    def _set_light_bright(self, id: str, bright: int) -> requests.Response:
        return requests.put(
            url=self._build_url(["lights", id, "state"]),
            data=json.dumps({"bri": bright})
        )

    def get_groups(self) -> requests.Response:
        return requests.get(
            url=self._build_url(["groups"])
        )

    def get_group_names(self) -> list:
        resp = self.get_groups()
        if resp.status_code != 200:
            print("Cannot reach Hue bridge to get Groups!")
            exit(1)
        return [group["name"] for group in resp.json().values()]

    def _get_group_id(self, name: str) -> str:
        group_name = self._group_name_from_alias(name)
        if group_name == "":
            print(f"ERROR:  Cannot find Group named {name}")
            exit(1)
        return str(self.group_map[group_name])

    def _group_name_from_alias(self, alias: str) -> str:
        for group, aliases in self.group_aliases.items():
            if alias == group.lower() or alias in aliases:
                return group
        return ""

    def get_group_by_name(self, name: str) -> requests.Response:
        return requests.get(
            url=self._build_url(["groups", self._get_group_id(name)])
        )

    def turn_on_group(self, name: str, bright=None) -> requests.Response:
        # If we are setting the brightness, we should set all the lights
        # before turning them on, otherwise use previous brightness
        if bright is not None:
            bright = self._clamp_brightness(bright)
        else:
            bright = self._clamp_brightness(100)
        group = self.get_group_by_name(name).json()
        for light_id in group["lights"]:
            resp = self._set_light_bright(light_id, bright)
            if resp.status_code != 200:
                print(f"ERROR: Couldn't access Light {light_id}")
        body = {"on": True, "bri": self._clamp_brightness(bright)}
        return requests.put(
            url=self._build_url(
                ["groups", self._get_group_id(name), "action"]
            ),
            data=json.dumps(body)
        )

    def turn_off_group(self, name: str) -> requests.Response:
        return requests.put(
            url=self._build_url(
                ["groups", self._get_group_id(name), "action"]
            ),
            data=json.dumps({"on": False})
        )
