# OTC CloudEye Prometheus Exporter
Prometheus exporter that gather metrics from Open Telekom Cloud resources over Cloud Eye API

### Environment Variables
Name     | Description | Possible Values | Default Value
---------|-------------|-----------------|-----------
REFRESH_TIME | Time in seconds that exporter wait's to gather metrics again | Integer >60 | 300
NAMESPACES | OTC Namespaces from which you want to get metrics | ECS,RDS,DDS,DMS,EVS,VPC,ELB... | -
PROJECT_ID | OTC Project ID that you can find on OTC GUI under `My Credential -> Project ID` | Valid Project ID | -
TENANT_NAME | OTC Tenant Name that you can find on OTC GUI under `My Credential -> Domain Name` | Valid Tenant/Domain Name | -
USERNAME | OTC Username with `Tenant Guest` role | Valid Username | - 
PASSWORD | OTC Password | Valid Password | - 
RANCHER_SECRETS | If set to `true`* the password will be replaced by the Rancher Secret with the name defined on the variable `$PASSWORD` | true or false | false
LOG_LEVEL | Exporter's log level | WARNING or INFO or DEBUG | INFO
\* On YML file (Docker Compose) you will need to use quotes like that: `RANCHER_SECRETS='true'`, otherwise the YML parser will parse it as a boolean and it will not work.

### Docker Compose
``` yaml
version: '3'

services:
  otc-exporter:
    restart: always
    image: tiagoreichert/otc-cloudeye-prometheus-exporter
    ports:
      - "8000:8000"
    environment:
      - REFRESH_TIME=300
      - NAMESPACES=ECS,DMS,RDS
      - PROJECT_ID=<projectid>
      - TENANT_NAME=OTC-EU-DE-<tentantnumber>
      - USERNAME=foo
      - PASSWORD=bar
      - LOG_LEVEL=DEBUG
```

### Prometheus YML Configuration
```yaml
  - job_name: 'OTC'
    scrape_interval: 60s
    metrics_path: "/"
    static_configs:
      - targets:
        - <otc-exporter-address>:8000
```

### Grafana Dashboards
Grafana Dashboards for some OTC services are available on the [Grafana Community catalog](https://grafana.com/orgs/tiagoreichert)

---

#### Known Limitations
For every metric value it's needed to make a request against the Cloud Eye API.
Unfortunately, there is no other way to gather metric information from the Cloud Eye API.
Bearing that in mind, take care to not include to much OTC resources, that can be
limited using the NAMESPACES environment parameter.

#### Kanban Board

[![Trello Board](https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Trello-logo-blue.svg/200px-Trello-logo-blue.svg.png)](https://trello.com/b/IgXJprlt)
