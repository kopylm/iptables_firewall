import json
import requests
import iptc


CONSUL_CATALOG_URL = "http://localhost:8500/v1/catalog/service/wireguard"
SERVICES_FILE = 'services.json'
FIREWALL_RULES = 'rules.json'


def get_catalog_info():
    data = requests.get(CONSUL_CATALOG_URL)
    return data.json()


def get_catalog_info_from_file():
    with open(SERVICES_FILE, 'r') as services_file:
        file_contents = services_file.read()
    return json.loads(file_contents)


def get_firewall_rules():
    with open(FIREWALL_RULES, 'r') as rules_file:
        file_contents = rules_file.read()
    return json.loads(file_contents)


# Get IPs of services that are allowed to initiate connections
def get_source_ips(data, fleets):
    source_ips = []

    if "*" in fleets:
        for service in data:
            source_ips.extend(service['ServiceAddress'])
    else:
        for fleet in fleets:
            for service in data:
                if service['NodeMeta']['env'] == fleet['env']:
                    source_ips.extend(service['ServiceAddress'])

    return source_ips


# Get IPs of services that are allowed to receive connections
def get_target_ips(data, fleets, stages):
    target_ips = []

    # for stage in stages:
    #     for fleet in fleets:
    return target_ips


# Create iptables rules
def generate_iptables_rules(data, rules):
    result = []

    for rule in rules['rules']:
        port = rule['port']
        envs = rule['env']
        stages = rule['stages']
        fleets = rule['fleets']

        source_ips = get_source_ips(data, fleets)
        target_ips = get_target_ips(data, fleets, stages)


if __name__ == "__main__":
    info = get_catalog_info_from_file()  # change function if we need to get info from consul service
    firewall_rules = get_firewall_rules()
    generate_iptables_rules(info, firewall_rules)


