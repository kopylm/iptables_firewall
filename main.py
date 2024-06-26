import json
import requests
import iptc
import socket
import os
from logger_config import setup_logger

logger = setup_logger()

NODES_DATA_FILE = 'nodes.json'
FIREWALL_RULES = 'rules.json'


# With NET_ADMIN capability and hostNetwork: true, hostPID: true should return host ip address
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        s.connect(('8.8.8.8', 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


# Mocked ip address for test
def get_mocked_host_ip():
    return os.environ['MOCKED_HOST_IP']


# Get catalog data from Consul
def get_catalog_info():
    try:
        data = requests.get(os.environ['CONSUL_CATALOG_URL'])
        logger.info('Successfully fetched catalog info from the Consul')
        return data.json()
    except Exception as e:
        logger.error(f"Error fetching catalog from the Consul: {e}")
        return []


# Mocked Consul catalog
def get_catalog_info_from_file():
    try:
        with open(NODES_DATA_FILE) as services_file:
            file_contents = services_file.read()
            logger.info('Successfully fetched catalog info from the file')
        return json.loads(file_contents)
    except Exception as e:
        logger.error(f"Error fetching catalog from the file: {e}")
        return []


# Get firewall rules from the file
def get_firewall_rules():
    try:
        with open(FIREWALL_RULES) as rules_file:
            file_contents = rules_file.read()
            logger.info('Loaded firewall rules')
        return json.loads(file_contents)
    except Exception as e:
        logger.error(f"Error loading firewall rules: {e}")
        return []


# Get IPs of nodes that are allowed to initiate connections
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
    logger.debug(f"Source IPs: {source_ips}")
    return source_ips


# Get IPs of nodes that are allowed to receive connections
def get_destination_ips(data, envs, stages):
    destination_ips = []

    for stage in stages:
        for env in envs:
            for service in data:
                if env == '*':
                    destination_ips.append(service['ServiceAddress'])
                else:
                    if service['NodeMeta']['env'] == env and service['NodeMeta']['stage'] == stage:
                        destination_ips.append(service['ServiceAddress'])
    logger.debug(f"Target IPs: {destination_ips}")
    return destination_ips


# Create iptables rules
def generate_iptables_rules(data, rules, current_host_ip):
    result = []

    for rule in rules['rules']:
        port = rule['port']
        envs = rule['env']
        stages = rule['stages']
        fleets = rule['fleets']

        source_ips = get_source_ips(data, fleets)
        target_ips = get_destination_ips(data, envs, stages)

        for target_ip in set(target_ips):
            if target_ip == current_host_ip:
                for source_ip in source_ips:
                    result.append((port, source_ip, target_ip))
    logger.info(f"Generated firewall rules: {result}")
    return result


def get_existing_rules():
    existing_rules = []
    table = iptc.Table(iptc.Table.FILTER)
    chain = iptc.Chain(table, "INPUT")

    for rule in chain.rules:
        for match in rule.matches:
            if match.name == "tcp":
                dport = int(match.dport)
                src = rule.src.split('/')[0]
                dst = rule.dst.split('/')[0]
                existing_rules.append((dport, src, dst))
    logger.info(f"Existing rules: {existing_rules}")
    return existing_rules


# Existing rules will not be added
# Rules which not in the rules.json will be deleted
def validate_rules(new_rules, existing_rules):
    rules_to_apply = [rule for rule in new_rules if rule not in existing_rules]
    rules_to_delete = [rule for rule in existing_rules if rule not in new_rules]
    logger.info(f"Valid rules to apply: {rules_to_apply}")
    logger.info(f"Rules to delete: {rules_to_delete}")
    return rules_to_apply, rules_to_delete


# Manage apply and delete actions
def manage_rule(port, source_ip, target_ip, action):
    table = iptc.Table(iptc.Table.FILTER)
    chain = iptc.Chain(table, "INPUT")

    rule = iptc.Rule()
    rule.protocol = "tcp"
    match = rule.create_match("tcp")
    match.dport = str(port)
    rule.src = source_ip
    rule.dst = target_ip
    rule.target = iptc.Target(rule, "ACCEPT")

    if action == "insert":
        chain.insert_rule(rule)
        logger.info(f"Applied rule: {port} {source_ip} {target_ip}")
    elif action == "delete":
        chain.delete_rule(rule)
        logger.info(f"Deleted rule: {port} {source_ip} {target_ip}")


def apply_firewall_rules(rules_to_apply, rules_to_delete):
    for port, source_ip, target_ip in rules_to_apply:
        manage_rule(port, source_ip, target_ip, "insert")
    for port, source_ip, target_ip in rules_to_delete:
        manage_rule(port, source_ip, target_ip, "delete")


def main(current_host_ip):
    catalog_data = get_catalog_info_from_file()  # change function if we need to get info from consul service
    if not catalog_data:
        logger.error("No catalog data found")
        exit(1)

    firewall_rules = get_firewall_rules()
    if not firewall_rules:
        logger.error("No firewall rules found")
        exit(1)

    generated_rules = generate_iptables_rules(catalog_data, firewall_rules, current_host_ip)
    exist_rules = get_existing_rules()
    validated_rules, rules_to_delete = validate_rules(generated_rules, exist_rules)
    apply_firewall_rules(validated_rules, rules_to_delete)


if __name__ == "__main__":
    host_ip = get_mocked_host_ip()
    if not host_ip:
        logger.error("Error getting host ip")

    logger.info(f"Host IP: {host_ip}")
    main(host_ip)
