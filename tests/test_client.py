import json

import pytest
from pyunifi_ng.client import Client, UnsupportedController

c = Client("admin", "admin", host="127.0.0.1", port=8443, verify=False)
b = Client("api_admin", "Test_API_Client_0", "192.168.1.40", verify=False)


def test_client():
    assert isinstance(c, Client)


def test_client_host():
    assert c.host == "127.0.0.1"


def test_request():
    assert c._base_url == "https://127.0.0.1:8443/"


def test_login_self_hosted():
    # Test Self Host
    c.login()
    assert not c.is_unifi_os
    assert c.login_path == "api/login"
    assert c.headers == None


def test_login_unifios():
    b.login()
    assert b.is_unifi_os
    assert b.login_path == "api/auth/login"
    assert b.headers["X-CSRF-Token"]


def test_update_policy():
    c.login()
    policies = c.get_firewall_policies()

    rule = [
        rule
        for rule in json.loads(policies.content)
        if rule.get("description") == "AU001"
    ].pop()

    rule["destination"].update({"web_domains": ["abc.com", "cnn.com", "meta.com"]})
    assert rule["destination"]["web_domains"] == ["abc.com", "cnn.com", "meta.com"]
    assert isinstance(rule["_id"], str)

    a = c.update_firewall_policies(id=rule["_id"], policy=rule)
    assert a.status_code == 200


def test_get_site_id():
    c.login()
    c.get_sites_overview()


# def _test_add_dhcp_reservation():
#     dev = {
#         "mac": "7b:58:09:58:6e:c3",
#         "name": "Test3",
#         "local_dns_record_enabled": False,
#         "fixed_ip": "192.168.1.123",
#         "use_fixedip": True,
#     }

#     c.login()
#     c.add_dhcp_reservation(dev)


#  https://127.0.0.1:8443/api/s/default/rest/user

c.login()
# d = json.loads(c.get_sites_overview(search_text=""))
# sites = {site["description"]: site["id"] for site in d.get("data")}

# dev = {
#     "mac": "7b:58:09:58:6e:c3",
#     "name": "Test3",
#     "local_dns_record_enabled": False,
#     "fixed_ip": "192.168.1.123",
#     "use_fixedip": True,
# }

dev = {
    "mac": "7b:58:09:58:6e:c3",
    "name": "Test Two",
    "use_fixedip": True,
    "local_dns_record_enabled": False,
    "fixed_ip": "192.168.1.123",
}


# c.add_dhcp_reservation(dev)


# {
#     "meta": {
#         "rc": "ok"
#     },
#     "data": [
#         {
#             "mac": "b4:75:ab:6e:7b:21",
#             "name": "Random Device",
#             "use_fixedip": true,
#             "local_dns_record_enabled": true,
#             "local_dns_record": "random.my.net",
#             "fixed_ip": "192.168.2.234",
#             "site_id": "6794935890319a363e9e197b",
#             "is_wired": true,
#             "is_guest": false,
#             "oui": "",
#             "noted": true,
#             "usergroup_id": "",
#             "_id": "67c2f8e89475d83b9fbaaa9a"
#         }
#     ]
# }
# # # extract rule
# # rule = [rule for rule in rules if rule.get("description") == "AU001"]
# # newdomains = ["abc.cn", "zxy.net"]
# # rule[0]["destination"].update({"web_domains": newdomains})
# # print(json.dumps(rule))

# # a = c.update_firewall_policies(id="1", policy=rules)
# # print(a)

# # print(f"firewall-polices/{rule[0]["_id"]}")
# # https://127.0.0.1:8443/v2/api/site/default/firewall-policies
# # https://unifi/proxy/network/v2/api/site/default/firewall-policies
