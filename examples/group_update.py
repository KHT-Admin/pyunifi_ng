from csv import DictReader
from typing import Generator

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
                if (k in {"mac", "group_name"}) & (v is not None)
            }
            for row in reader
        ]
    return data


def extract_group_names(data) -> set:
    return {dd for device in data if (dd := device.get("group_name", None)) is not None}


def get_existing_groups(apiclient) -> dict:
    return {
        group.get("name"): group.get("id")
        for group in apiclient.get_network_members_groups()
    }


def find_missing_groups(groups: set, existing: dict) -> set:
    return groups - {*existing}


def add_missing_group(missing, apiclient):
    for group in missing:
        apiclient.add_network_members_group(group)


def build_member_lists(clients) -> dict:
    return {
        gn: [c["mac"] for c in clients if c["group_name"] == gn]
        for gn in {client["group_name"] for client in clients}
    }


def update_group_membership(
    grouped_macs: dict,
    groups: dict,
    apiclient,
):
    for k, v in grouped_macs.items():
        apiclient.update_network_members_group(group_id=groups[k], name=k, members=v)


def process(CSVFILE: str, apiclient: pyunifi_ng):
    clients = read_csv(CSVFILE)

    add_missing_group(
        find_missing_groups(
            extract_group_names(clients),
            get_existing_groups(apiclient),
        ),
        apiclient,
    )

    # update groups listing
    update_group_membership(
        build_member_lists(clients),
        get_existing_groups(apiclient),
        apiclient,
    )


def main():
    client = pyunifi_ng.Client(USER, PWD, host=HOST, port=PORT)

    client.login()
    process(CSVFILE, client)
    client.logout()


if __name__ == "__main__":
    main()
