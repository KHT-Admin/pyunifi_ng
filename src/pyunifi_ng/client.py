from enum import Enum
from typing import Optional, Union

import requests
import urllib3


class UniFiNgError(Exception):
    """Base exception for API"""


class APIError(UniFiNgError):
    """general error message"""


class UnsupportedController(UniFiNgError):
    """Not supported"""


class API:
    v1 = "api/s"
    v2 = "v2/api/site"
    v2b = "v2/api"


class Client:
    def __init__(
        self,
        username: str,
        password: str,
        host: str = "127.0.0.1",
        port: int = 443,
        verify: bool = False,
        site_id="default",
    ):
        self.username: str = username
        self.password: str = password
        self.host: str = host
        self.port: int = port
        self.verify: bool = verify
        self.is_unifi_os: bool = False
        self.session: Optional[requests.Session] = None
        self.headers = None
        self.site_id = site_id

    def logout(self):
        self._request(
            "post",
            f"{self._base_url}{self.auth_path}/logout",
        )
        self.session.close()

    def login(self):
        if self.verify is False:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.session = requests.Session()
        self.session.verify = self.verify

        self._verify_network_type()
        self._api_authenticate()

    @property
    def _base_url(self) -> str:
        url = f"https://{self.host}:{self.port}/"
        return url

    @staticmethod
    def _jsondecode(response) -> dict:
        obj = response.json()

        if "meta" in obj and obj["meta"]["rc"] != "ok":
            raise APIError(obj["meta"]["msg"])

        return obj.get("data", obj)

    def _request(self, fn, url, params=None):
        if params is None:
            return getattr(self.session, fn)(
                url,
                headers=self.headers,
            )
        else:
            return getattr(self.session, fn)(
                url,
                **params,
                headers=self.headers,
            )

    def _update_tokens(self, header: dict) -> None:
        if "X-CSRF-Token" in header:
            self.headers = {"X-CSRF-Token": header["X-CSRF-Token"]}

    def _response_process(self, response) -> dict:
        # Catch http error response
        response.raise_for_status()

        self._update_tokens(response.headers)
        return response
        # return self._jsondecode(response)

    def _api_url(self, api: API, site_id):
        if self.is_unifi_os:
            api = f"proxy/network/{api}"

        if site_id is None:
            site = f"/{self.site_id}/"
        elif site_id == "":
            site = "/"
        else:
            site = f"/{site_id}/"

        return f"{self._base_url}{api}{site}"

    def _api_authenticate(self):
        try:
            response = self._request(
                "post",
                f"{self._base_url}{self.auth_path}/login",
                {
                    "json": {
                        "username": self.username,
                        "password": self.password,
                    }
                },
            )
        except (RequestException, ConnectTimeout) as e:
            print(e)
            exit(1)

        self._update_tokens(response.headers)

        if response.status_code != 200:
            raise APIError("Login failed - status code: %i" % response.status_code)

    def _api_base(
        self,
        method,
        url,
        api: API,
        params: Optional[dict] = None,
        site_id: Optional[str] = None,
    ):
        return self._request(
            method,
            f"{self._api_url(api, site_id)}{url}",
            params,
        )

    def _api_read(
        self,
        url,
        api: API,
        params: Optional[dict] = None,
        site_id: Optional[str] = None,
    ):
        return self._response_process(self._api_base("get", url, api, params, site_id))

    def _api_write(
        self,
        url,
        api: API,
        params: Optional[str] = None,
        site_id: Optional[str] = None,
    ):
        return self._response_process(self._api_base("post", url, api, params, site_id))

    def _api_update(
        self,
        url,
        api: API,
        params: Optional[str] = None,
        site_id: Optional[str] = None,
    ):
        return self._response_process(self._api_base("put", url, api, params))

    def _api_delete(
        self,
        url,
        api: API,
        params=None,
    ):
        return self._response_process(self._api_base("delete", url, api, params))

    def _verify_network_type(self):
        """
        Silence certificate warnings when verification is false
        """
        for p in {"api", "network"}:
            if self.session.request("get", f"{self._base_url}{p}").status_code == 200:
                break

        else:
            raise UnsupportedController("Host is not a supported controller")

        if p == "network":
            self.is_unifi_os = True
            self.auth_path = "api/auth"
        else:
            self.auth_path = "api"

    def get_sites_overview(
        self,
        pageSize: int = 1000,
        pageNumber: int = 0,
        searchText: str = "",
        _id: str = "",
    ):
        return self._api_write(
            "sites/overview",
            params={
                "json": {
                    "pageSize": pageSize,
                    "pageNumber": pageNumber,
                    "searchText": searchText,
                },
            },
            api=API.v2b,
            site_id=_id,
        ).json()

    def get_site_ids(self, search_text=""):
        r = self.get_sites_overview(search_text)

    def get_devices(self) -> list[dict]:
        """
        Return a list of all active UniFi devices
        """
        return self._api_read("device", api=API.v2)

    def get_clients(self):
        return self._api_read("clients/active", api=API.v2)

    def get_client_history(
        self,
        onlyNonBlocked=True,
        includeUnifiDevices=True,
        withinHours=0,
    ):
        return self._api_read(
            "clients/history",
            params={
                "params": {
                    "onlyNonBlocked": onlyNonBlocked,
                    "includeUnifiDevices": includeUnifiDevices,
                    "withinHours": withinHours,
                }
            },
            api=API.v2,
        )

    def get_firewall_policies(
        self,
        id: Optional[str] = None,
    ) -> list[dict] | dict:
        return self._api_read(
            f"firewall-policies/{id}" if id else "firewall-policies",
            api=API.v2,
        )

    def update_firewall_policies(
        self,
        id: str,
        policy: dict,
    ):
        if not isinstance(policy, dict):
            raise ValueError

        return self._api_update(
            f"firewall-policies/{id}" if id else "firewall-policies",
            params={
                "json": policy,
            },
            api=API.v2,
        )

    def add_dhcp_reservation(self, data: dict):
        self._api_write(
            "rest/user",
            params={
                "json": data,
            },
            api=API.v1,
        )

    def add_network_members_group(
        self,
        name: str,
        members: list = [],
        type="CLIENTS",
    ):
        ### {"name":"NAME","members":[],"type":"CLIENTS"}
        self._api_write(
            "network-members-group",
            params={
                "json": {
                    "name": name,
                    "members": members,
                    "type": type,
                },
            },
            api=API.v2,
        )

    def get_network_members_groups(self):
        return self._api_read(
            "network-members-groups",
            api=API.v2,
        ).json()

    def update_network_members_group(
        self,
        group_id: str,
        name: str,
        members: list = [],
        type="CLIENTS",
    ):
        self._api_write(
            "network-members-group",
            params={
                "json": {
                    "id": group_id,
                    "name": name,
                    "members": members,
                    "type": type,
                },
            },
            api=API.v2,
        )
