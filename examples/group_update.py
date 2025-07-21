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


def get_groups(apiclient):
    return apiclient.get_network_members_groups()


def get_existing_groups(apiclient) -> dict:
    return {group.get("name"): group.get("id") for group in get_groups(apiclient)}


def get_group_members(apiclient) -> dict:
    return {group.get("name"): group.get("members") for group in get_groups(apiclient)}


def find_missing_groups(groups: set, existing: dict) -> set:
    return groups - {*existing}


def add_missing_group(missing, apiclient):
    for group in missing:
        apiclient.add_network_members_group(group)


def build_member_lists(clients) -> dict:
    return {
        gn: [c["mac"].lower() for c in clients if c["group_name"] == gn]
        for gn in {client["group_name"] for client in clients}
    }


def update_group_membership(
    grouped_macs: dict,
    groups: dict,
    apiclient,
):
    current = get_group_members(apiclient)

    for k, v in grouped_macs.items():
        v.extend(current[k])
        apiclient.update_network_members_group(
            group_id=groups[k], name=k, members=list(set(v))
        )


def process(CSVFILE: str, apiclient: pyunifi_ng):
    clients = read_csv(CSVFILE)

    add_missing_group(
        find_missing_groups(
            extract_group_names(clients),
            get_existing_groups(apiclient),
        ),
        apiclient,
    )

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
