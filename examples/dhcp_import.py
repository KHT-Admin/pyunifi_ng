import argparse
import re

import pyunifi_ng.client as pyunifi_ng
import requests

ER = r"static-mapping\s+(?P<name>[a-zA-Z0-9\s\-_\.]+)[\W\w]+?(?P<fixed_ip>(?:[0-9]{1,3}\.?){4})[\W\w]+?(?P<mac>(?:[0-9a-fA-Fx]{2}\:?){6})"
OPNS = r"<staticmap>[\W\w]+?(?P<mac>(?:[0-9a-fA-Fx]{2}\:?){6})[\W\w]+?(?P<fixed_ip>(?:[0-9]{1,3}\.?){4})[\W\w]+?<hostname>(?P<name>.+?)</hostname>[\W\w]+?<descr>(?P<note>.+?)</descr>"


def read_file(path: str) -> str:
    with open(path, "r") as f:
        data = f.read()
    return data


def extract_static(data: str, pattern):
    decoder = OPNS if pattern == "OPNS" else ER

    return re.finditer(
        decoder,
        data,
        re.I,
    )


def device_encode(data: iter) -> list[dict]:
    reservations = []
    for res in data:
        device = res.groupdict()

        if "fixed_ip" in device:
            device.update({"use_fixedip": True})

        if "local_dns_record" in device:
            device.update({"local_dns_record_enabled": True})

        reservations.append(device)
    return reservations


def device_upload(data: list[dict], c) -> dict:
    failed = []
    c.login()
    for record in data:
        try:
            c.add_dhcp_reservation(record)
        except requests.exceptions.HTTPError:
            """API returns error if subnet is not configured or reservation exists"""
            failed.append(record)
    return {"n_failed": len(failed), "failed": failed}


def process(path: str, pattern, client):
    s = extract_static(read_file(path), pattern=pattern)
    d = device_encode(s)

    return device_upload(d, client)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("decoder", choices=["ER", "OPNS"], help="config type")
    parser.add_argument("user", help="username")
    parser.add_argument("pwd", help="password")
    parser.add_argument("host")
    parser.add_argument("--port", type=int, choices=[443, 8443])

    return parser.parse_args()


def main():
    a = parse_args()
    c = pyunifi_ng.Client(a.user, a.pwd, host=a.host, port=a.port)

    r = process(a.path, a.decoder, c)
    print(r)


if __name__ == "__main__":
    main()
