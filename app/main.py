#!/usr/bin/python
# coding=utf-8
# -------------------------------------------------------------
#       OTC CloudEye Prometheus Exporter
#
#       Author: Tiago M Reichert
#       Initial Release: 04/08/2018
#       Email: tiago@reichert.eti.br
#       Version: v0.1a
# --------------------------------------------------------------
import requests
import json
from datetime import datetime
import configparser
import logging
import logging.config
from prometheus_client import start_http_server, Gauge
import time


def main():
    # Logging configuration
    logging.config.fileConfig('/app/config/log_config.ini')

    # Reading configuration file
    global config
    config = configparser.ConfigParser()
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
        metrics = get_available_metrics()
        get_metric_value(prometheus_metrics=prometheus_metrics, metrics=metrics)
        time.sleep(float(config.get('EXPORTER_CONFIG', 'refresh_time')))


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
        metric_name = "%s_%s" % (namespace.replace(".", "_"), m["metric_name"])
        dimensions_name = m["dimensions"][0]["name"]
        # Check if metric was not already created
        if "%s:%s" % (namespace, m["metric_name"]) not in prometheus_metrics.keys():
            vars()[metric_name] = Gauge('OTC_CES_%s' % metric_name, metric_name, ["unit", dimensions_name])
            prometheus_metrics["%s:%s" % (namespace, m["metric_name"])] = eval(metric_name)
    return prometheus_metrics


def get_metric_value(prometheus_metrics, metrics):
    current_time = get_current_metrics_time()
    cloud_eye_base = config.get('OTC_ENDPOINTS', 'cloud_eye_base')

    # For each OTC metric from the defined Namespaces
    for m in metrics:
        namespace = m["namespace"]
        metric_name = m["metric_name"]
        dimensions_name = m["dimensions"][0]["name"]
        dimensions_value = m["dimensions"][0]["value"]
        full_metric_name = "%s:%s" % (namespace, metric_name)

        url = "{0}?namespace={1}&metric_name={2}&dim.0={3},{4}&from={5}&to={6}&period=300" \
              "&filter=average".format(cloud_eye_base, namespace, metric_name, dimensions_name, dimensions_value,
                                       current_time[0], current_time[1])

        time.sleep(0.1)  # Wait for 100 milliseconds before every request (needed to don't overload OTC API)
        r = requests.get(url, headers={'X-Auth-Token': get_token()})

        if r.status_code == 200:
            resp = json.loads(r.text)
            if resp['datapoints']:
                logging.debug("{0} for '{1}={2}' at {3} : {4}".format(full_metric_name, dimensions_name,
                                                                      dimensions_value, datetime.fromtimestamp
                                                                      (resp['datapoints'][0]['timestamp'] / 1000.0),
                                                                      resp['datapoints'][0]['average']))

                exec("prometheus_metrics[full_metric_name].labels(unit=resp['datapoints'][0]['unit'], "
                     "%s=dimensions_value).set(resp['datapoints'][0]['average'])") % dimensions_name

        elif r.status_code == 401:
            logging.warn("Token seems to be expired, requesting a new one and retrying")
            request_token()
            get_metric_value(prometheus_metrics=prometheus_metrics, metrics=metrics)
            break
        else:
            logging.error("Request for metric '%s' value got result code '%s'" % (full_metric_name, r.status_code))


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
        f = open('/app/config/app_config.ini', 'w')
        try:
            config.write(f)
        finally:
            f.close()
        logging.info("New token generated")
        return r.headers['x-subject-token']
    else:
        logging.error("Request for token got result code '%s'" % r.status_code)
        exit(2)


if __name__ == '__main__':
    main()
