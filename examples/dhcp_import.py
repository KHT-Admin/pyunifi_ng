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
    return re.finditer(
        pattern,
        data,
        re.I,
    )


def device_upload(data: list[dict]) -> dict:
    failed = []
    for record in data:
        try:
            c.add_dhcp_reservation(record)
        except requests.exceptions.HTTPError:
            """API returns error if subnet is not configured or reservation exists"""
            failed.append(record)
    return {"n_failed": len(failed), "failures": failed}


def device_encode(data: iter) -> list[dict]:
    reservations = []
    for res in data:
        device = res.groupdict()

        if "fixed_ip" in device:
            device.update({"use_fixedip": True})
        else:
            device.update({"use_fixedip": False})

        if "local_dns_record" in device:
            device.update({"local_dns_record_enabled": True})

        reservations.append(device)
    return reservations


def process(path: str, pattern):
    s = extract_static(read_file(path), pattern=pattern)
    d = device_encode(s)
    return device_upload(d)


path = "../tests/opnsense.xml"

c = pyunifi_ng.Client("admin", "admin", host="127.0.0.1", port=8443)
c.login()

err = process(path, OPNS)
print(err)
