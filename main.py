import json
import requests
import iptc
import logging


CONSUL_CATALOG_URL = "http://localhost:8500/v1/catalog/service/wireguard"
SERVICES_FILE = 'services.json'
FIREWALL_RULES = 'rules.json'


def get_catalog_info():
    data = requests.get(CONSUL_CATALOG_URL)
    return data.json()


def get_catalog_info_from_file():
    with open(SERVICES_FILE) as services_file:
        file_contents = services_file.read()
    return json.loads(file_contents)


def get_firewall_rules():
    with open(FIREWALL_RULES) as rules_file:
        file_contents = rules_file.read()
    return json.loads(file_contents)


# Get IPs of services that are allowed to initiate connections
def get_source_ips(data, fleets):
    source_ips = []

    if "*" in fleets:
        for service in data:
            source_ips.append(service['ServiceAddress'])
    else:
        for fleet in fleets:
            for service in data:
                if service['NodeMeta']['env'] == fleet:
                    source_ips.append(service['ServiceAddress'])

    return source_ips


# Get IPs of services that are allowed to receive connections
def get_target_ips(data, envs, stages):
    target_ips = []

    for stage in stages:
        for env in envs:
            for service in data:
                if env == '*':
                    target_ips.append(service['ServiceAddress'])
                else:
                    if service['NodeMeta']['env'] == env and service['NodeMeta']['stage'] == stage:
                        target_ips.append(service['ServiceAddress'])

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
        target_ips = get_target_ips(data, envs, stages)

        for target_ip in set(target_ips):
            for source_ip in source_ips:
                result.append((port, source_ip, target_ip))

    return result


def get_existing_rules():
    table = iptc.Table(iptc.Table.FILTER)
    chain = iptc.Chain(table, "INPUT")
    existing = []

    for rule in chain.rules:
        if rule.protocol == "tcp":
            match = rule.get_match("tcp")
            if match:
                existing.append((int(match.dport), rule.src, rule.dst))

    return existing


def validate_rules(new_rules, existing_rules):
    valid_rules = []
    for rule in new_rules:
        if rule not in existing_rules:
            valid_rules.append(rule)
    return valid_rules


def apply_firewall_rules(rules):
    table = iptc.Table(iptc.Table.FILTER)
    chain = iptc.Chain(table, "INPUT")

    # Apply new rules
    for port, source_ip, target_ip in rules:
        rule = iptc.Rule()
        rule.protocol = "tcp"
        match = rule.create_match("tcp")
        match.dport = str(port)
        rule.src = source_ip
        rule.dst = target_ip
        rule.target = iptc.Target(rule, "ACCEPT")
        chain.insert_rule(rule)


if __name__ == "__main__":
    info = get_catalog_info_from_file()  # change function if we need to get info from consul service
    firewall_rules = get_firewall_rules()
    generated_rules = generate_iptables_rules(info, firewall_rules)
    exist_rules = get_existing_rules()
    validated_rules = validate_rules(generated_rules, exist_rules)
    apply_firewall_rules(validated_rules)
