import re

import pyunifi_ng.client as pyunifi_ng
import requests

ER = r"static-mapping\s+(?P<host>[a-zA-Z0-9\s\-_\.]+)[\W\w]+?(?P<ip>(?:[0-9]{1,3}\.?){4})[\W\w]+?(?P<mac>(?:[0-9a-fA-Fx]{2}\:?){6})"
OPNS = r"<staticmap>[\W\w]+?(?P<mac>(?:[0-9a-fA-Fx]{2}\:?){6})[\W\w]+?(?P<ip>(?:[0-9]{1,3}\.?){4})[\W\w]+?<hostname>(?P<host>.+?)</hostname>[\W\w]+?<descr>(?P<note>.+?)</descr>"


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


def device_mapping(data: iter) -> dict:
    failed = []
    for res in data:
        r = res.groupdict()

        device = {
            "mac": r.get("mac"),
            "name": r.get("host"),
            "use_fixedip": True,
            "local_dns_record_enabled": False,
            "fixed_ip": r.get("ip"),
        }

        if "note" in r:
            device.update({"note": r.get("note")})

        try:
            c.add_dhcp_reservation(device)
        except requests.exceptions.HTTPError:
            """API returns error if subnet is not configured or reservation exists"""
            failed.append(device)
    return {"n_failed": len(failed), "failures": failed}


c = pyunifi_ng.Client("admin", "admin", host="127.0.0.1", port=8443)
c.login()

path = "../tests/opnsense.xml"
dhcp_static = extract_static(read_file(path), pattern=OPNS)

f = device_mapping(dhcp_static)
print(f)
