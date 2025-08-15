from csv import DictReader

import pyunifi_ng.client as pyunifi_ng
import requests

# Configuration

USER = "admin"
PWD = "admin"
HOST = "127.0.0.1"
PORT = "8443"  # Use '443" for unifi consoles
CSVFILE = "fixedip.csv"


def read_csv(csvfile: str) -> list[dict]:
    with open(csvfile, "r") as f:
        reader = DictReader(f)
        data = [
            {
                k: v
                for k, v in row.items()
                if (k in {"mac", "fixed_ip", "name", "local_dns_record", "note"})
                & (v != "")
            }
            for row in reader
        ]
    return data


def device_encode(data: list[dict]) -> list[dict]:
    for device in data:
        if device.get("fixed_ip"):
            device.update({"use_fixedip": True})

        if device.get("local_dns_record"):
            device.update({"local_dns_record_enabled": True})

    return data


def device_upload(data: list[dict], client: pyunifi_ng.Client) -> dict:
    failed = []

    for record in data:
        try:
            client.add_dhcp_reservation(record)
        except requests.exceptions.HTTPError:
            """API returns error if subnet is not configured or reservation exists"""
            failed.append(record)
    return {"n_failed": len(failed), "failed": failed}


def process(path: str, apiclient):
    clients = read_csv(path)
    devices = device_encode(clients)
    return device_upload(devices, apiclient)


def main():
    apiclient = pyunifi_ng.Client(USER, PWD, host=HOST, port=PORT)

    apiclient.login()
    failed = process(CSVFILE, apiclient)
    apiclient.logout()

    # print failures
    print(failed)


if __name__ == "__main__":
    main()
