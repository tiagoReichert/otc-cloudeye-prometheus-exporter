#!/usr/bin/python
# coding=utf-8
# -------------------------------------------------------------
#       OTC CloudEye Prometheus Exporter
#
#       Author: Tiago M Reichert
#       Initial Release: 04/08/2018
#       Email: tiago@reichert.eti.br
#       Version: v0.2a
#       Contributor: Johannes Grumboeck <johannes@grumboeck.net>
# --------------------------------------------------------------
import requests
import json
from datetime import datetime
import configparser
import logging
import logging.config
from prometheus_client import start_http_server, Gauge
import time
config = configparser.ConfigParser()


def main():
    # Logging configuration
    logging.config.fileConfig('/app/config/log_config.ini')

    # Reading configuration file
    global config
    config._interpolation = configparser.ExtendedInterpolation()
    f = open('/app/config/app_config.ini')
    try:
        config.read_file(f)
    finally:
        f.close()

    start_http_server(8000)

    # Generate Prometheus Metrics
    metrics = get_available_metrics()
    prometheus_metrics = generate_prometheus_metrics(metrics=metrics)

    # Endless loop gathering metrics (sleep's for time defined on config file)
    while True:
        get_name_mapping()
        metrics = get_available_metrics()
        get_metric_value(prometheus_metrics=prometheus_metrics, metrics=metrics)
        time.sleep(float(config.get('EXPORTER_CONFIG', 'refresh_time')))


def get_name_mapping():
    namespaces = config.get('EXPORTER_CONFIG', 'namespaces').split(',')
    if "ECS" in namespaces:
        get_ecs_mapping()
    if "DMS" in namespaces:
        get_dms_mapping()
    if "RDS" in namespaces:
        get_rds_mapping()
    if "ELB" in namespaces:
        get_elb_mapping()
    if "NAT" in namespaces:
        get_nat_mapping()


def get_dms_mapping():
    r = requests.get(config.get('OTC_ENDPOINTS', 'dms_names'), headers={'X-Auth-Token': get_token()})
    if r.status_code == 200:
        for queue in json.loads(r.text)["queues"]:
            config.set('DMS_IDS', queue['id'], queue['name'])
            logging.debug("Created name entry for DMS '%s'='%s' successfully" % (queue['id'], queue['name']))
            consumer_group_url = config.get('OTC_ENDPOINTS', 'dms_consumer_names').replace("<queue_id>", queue['id'])
            r = requests.get(consumer_group_url, headers={'X-Auth-Token': get_token()})
            if r.status_code == 200:
                for group in json.loads(r.text)["groups"]:
                    group_name = '%s/%s' % (queue['name'], group['name'])
                    config.set('DMS_IDS', group['id'], group_name)
                    logging.debug("Created name entry for DMS Group '%s'='%s' successfully" % (group['id'], group_name))
        save_config_file()
    elif r.status_code == 401:
        logging.warn("Token seems to be expired, requesting a new one and retrying")
        request_token()
        get_dms_mapping()
    else:
        logging.error("Could not gather DMS names, got result code '%s'" % r.status_code)


def get_rds_mapping():
    r = requests.get(config.get('OTC_ENDPOINTS', 'rds_names'), headers={'X-Auth-Token': get_token(),
                                                                        'Content-Type': 'application/json',
                                                                        'X-Language': 'en-us'})
    if r.status_code == 200:
        for instance in json.loads(r.text)["instances"]:
            config.set('RDS_IDS', instance['id'], instance['name'])
            logging.debug("Created name entry for RDS '%s'='%s' successfully" % (instance['id'], instance['name']))
        save_config_file()
    elif r.status_code == 401:
        logging.warn("Token seems to be expired, requesting a new one and retrying")
        request_token()
        get_rds_mapping()
    else:
        logging.error("Could not gather RDS names, got result code '%s'" % r.status_code)


def get_ecs_mapping():
    r = requests.get(config.get('OTC_ENDPOINTS', 'ecs_names'), headers={'X-Auth-Token': get_token()})
    if r.status_code == 200:
        for server in json.loads(r.text)["servers"]:
            config.set('ECS_IDS', server['id'], server['name'])
            logging.debug("Created name entry for ECS '%s'='%s' successfully" % (server['id'], server['name']))
        save_config_file()
    elif r.status_code == 401:
        logging.warn("Token seems to be expired, requesting a new one and retrying")
        request_token()
        get_ecs_mapping()
    else:
        logging.error("Could not gather ECS names, got result code '%s'" % r.status_code)


def get_elb_mapping():
    r = requests.get(config.get('OTC_ENDPOINTS', 'elb_names'), headers={'X-Auth-Token': get_token()})
    if r.status_code == 200:
        for loadbalancer in json.loads(r.text)["loadbalancers"]:
            config.set('ELB_IDS', loadbalancer['id'], loadbalancer['name'])
            logging.debug("Created name entry for ELB '%s'='%s' successfully" % (loadbalancer['id'], loadbalancer['name']))
        save_config_file()
    elif r.status_code == 401:
        logging.warn("Token seems to be expired, requesting a new one and retrying")
        request_token()
        get_elb_mapping()
    else:
        logging.error("Could not gather ELB names, got result code '%s'" % r.status_code)

def get_nat_mapping():
    r = requests.get(config.get('OTC_ENDPOINTS', 'nat_names'), headers={'X-Auth-Token': get_token()})
    if r.status_code == 200:
        for nat_gateway in json.loads(r.text)["nat_gateways"]:
            config.set('NAT_IDS', nat_gateway['id'], nat_gateway['name'])
            logging.debug("Created name entry for NAT '%s'='%s' successfully" % (nat_gateway['id'], nat_gateway['name']))
        save_config_file()
    elif r.status_code == 401:
        logging.warn("Token seems to be expired, requesting a new one and retrying")
        request_token()
        get_nat_mapping()
    else:
        logging.error("Could not gather NAT names, got result code '%s'" % r.status_code)

def get_available_metrics():
    r = requests.get(config.get('OTC_ENDPOINTS', 'available_metrics'), headers={'X-Auth-Token': get_token()})
    if r.status_code == 200:
        metrics = []
        wanted_namespaces = ['SYS.%s' % n for n in config.get('EXPORTER_CONFIG', 'namespaces').split(',')]
        for metric in json.loads(r.text)["metrics"]:
            if metric["namespace"] in wanted_namespaces:
                metrics.append(metric)
        return metrics
    elif r.status_code == 401:
        logging.warn("Token seems to be expired, requesting a new one and retrying")
        request_token()
        return get_available_metrics()
    else:
        logging.error("Could not gather available metrics, got result code '%s'" % r.status_code)


def generate_prometheus_metrics(metrics):
    prometheus_metrics = {}
    for m in metrics:
        namespace = m["namespace"]
        metric_name = ("%s_%s" % (namespace.replace(".", "_"), m["metric_name"])).lower()
        # Check if metric was not already created
        if "%s:%s" % (namespace, m["metric_name"]) not in prometheus_metrics.keys():
            vars()[metric_name] = Gauge('otc_ces_%s' % metric_name, metric_name, ["unit", "resource_id",
                                                                                  "resource_name"])
            prometheus_metrics["%s:%s" % (namespace, m["metric_name"])] = eval(metric_name)
    return prometheus_metrics


def get_metric_value(prometheus_metrics, metrics):
    current_time = get_current_metrics_time()
    cloud_eye_base = config.get('OTC_ENDPOINTS', 'cloud_eye_base')

    # For each OTC metric from the defined Namespaces
    for idx, m in enumerate(metrics, start=1):
        # After every 10 metrics sleep for 1 seconds (otherwise OTC API get's overloaded)
        if idx % 10 == 0:
            time.sleep(1)

        namespace = m["namespace"]
        metric_name = m["metric_name"]
        dimensions_name = m["dimensions"][0]["name"]
        dimensions_value = m["dimensions"][0]["value"]
        full_metric_name = "%s:%s" % (namespace, metric_name)

        # For ELB skip metrics per listener, as I don't know how to represent them yet and they would overwrite the overall ELB metric
        if namespace == "SYS.ELB" and len(m["dimensions"]) > 1:
            continue

        url = "{0}?namespace={1}&metric_name={2}&dim.0={3},{4}&from={5}&to={6}&period=300" \
              "&filter=average".format(cloud_eye_base, namespace, metric_name, dimensions_name, dimensions_value,
                                       current_time[0], current_time[1])

        time.sleep(0.1)  # Wait for 100 milliseconds before every request (needed to don't overload OTC API)
        r = requests.get(url, headers={'X-Auth-Token': get_token()})

        if r.status_code == 200:
            resp = json.loads(r.text)
            if resp['datapoints']:
                resource_name = get_resource_name(resource_kind=namespace.replace("SYS.", ""),
                                                  resource_id=dimensions_value)

                prometheus_metrics[full_metric_name].labels(unit=resp['datapoints'][0]['unit'],
                                                            resource_id=dimensions_value,
                                                            resource_name=resource_name).set(resp['datapoints'][0]['average'])

                logging.debug("{0} for '{1}={2}' ({3}) at {4} : {5}".format(full_metric_name, dimensions_name,
                                                                            dimensions_value, resource_name,
                                                                            datetime.fromtimestamp(resp['datapoints'][0]['timestamp'] / 1000.0),
                                                                            resp['datapoints'][0]['average']))

        elif r.status_code == 401:
            logging.warn("Token seems to be expired, requesting a new one and retrying")
            request_token()
            get_metric_value(prometheus_metrics=prometheus_metrics, metrics=metrics)
            break
        else:
            logging.error("{0} for '{1}={2}' at {3} got HTTP Status Code: {4}".format(full_metric_name, dimensions_name,
                                                                                      dimensions_value, current_time,
                                                                                      r.status_code))


# Check if we have a name for the specified resource, if not return id
def get_resource_name(resource_kind, resource_id):
    if config.has_option("%s_IDS" % resource_kind, resource_id):
        return config.get("%s_IDS" % resource_kind, resource_id)
    else:
        logging.warn("Resource name for %s %s not found" % (resource_kind, resource_id))
        return resource_id


# Returns two time values in milliseconds with an difference of 1 second (needed by OTC API)
def get_current_metrics_time():
    current_time = int(round(time.time() * 1000))
    return current_time-1000, current_time


def get_token():
    if config.has_option('OTC_CREDENTIALS', 'token'):
        return config.get('OTC_CREDENTIALS', 'token')
    else:
        return request_token()


def request_token():
    r = requests.post(config.get('OTC_ENDPOINTS', 'request_token'),
                      json=json.loads(config.get('JSON_REQUEST', 'token')))
    if r.status_code == 201:
        config.set('OTC_CREDENTIALS', 'token', r.headers['x-subject-token'])
        save_config_file()
        logging.info("New token generated")
        return r.headers['x-subject-token']
    else:
        logging.error("Request for token got result code '%s'" % r.status_code)
        exit(2)


def save_config_file():
    f = open('/app/config/app_config.ini', 'w')
    try:
        config.write(f)
        logging.debug("Configuration file successfully saved")
    finally:
        f.close()


if __name__ == '__main__':
    main()
