import socket

from pyunifi_ng.client import Client, UnsupportedController


# https://stackoverflow.com/a/66000439
def get_ipv4_by_hostname(hostname):
    # see `man getent` `/ hosts `
    # see `man getaddrinfo`

    return list(
        i[4][0]  # raw socket structure  # internet protocol info  # address
        for i in socket.getaddrinfo(hostname, 0)  # port, required
        if i[0] is socket.AddressFamily.AF_INET  # ipv4
        # ignore duplicate addresses with other socket types
        and i[1] is socket.SocketKind.SOCK_DGRAM
    )


wl = get_ipv4_by_hostname("example.com")


c = Client(
    "apitest",
    "apitest",
    host="127.0.0.1",
    port=8443,
    verify=False,
    site_name="Default",
)

c.login()

policies = c.get_firewall_policies()

# Filter policies by description
# Use id string in description as search key - "wl001" for eg.

rule = [rule for rule in policies.json() if rule.get("description") == "wl001"].pop()

# Replace IPs with blocklist contents
rule["source"].update({"ips": wl})

# Update controller
c.update_firewall_policies(id=rule["_id"], policy=rule)
