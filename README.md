# OTC CloudEye Prometheus Exporter
Prometheus exporter that gather metrics from Open Telekom Cloud resources over Cloud Eye API


### Environment Variables
- REFRESH_TIME: Time that exporter wait's until gather metrics again, value in seconds (min 300) [default: 300]
- NAMESPACES: OTC Namespaces from which you want to get metrics (Example: DMS,ECS,RDS)
- PROJECT_ID: OTC Project ID
- TENANT_NAME: OTC Tenant Name
- USERNAME: OTC Username
- PASSWORD: OTC Password
- LOG_LEVEL: Exporter's log level (Example: WARNING, INFO, DEBUG) [default: INFO]

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
      - NAMESPACES=ECS,DMS
      - PROJECT_ID=<projectid>
      - TENANT_NAME=OTC-EU-DE-<tentantnumber>
      - USERNAME=foo
      - PASSWORD=bar
      - LOG_LEVEL=DEBUG
```

### Prometheus YML Configuration
```yaml
  - job_name: 'OTC'
    scrape_interval: 300s
    metrics_path: "/"
    static_configs:
      - targets:
        - <otc-exporter-address>:8000
```

#### Known Limitations
For every metric value it's needed to make a request against the Cloud Eye API.
Unfortunately, there is no other way to gather metric information from the Cloud Eye API.
Bearing that in mind, take care to not include to much OTC resources, that can be
limited using the NAMESPACES environment parameter.

#### TODO's
- [ ] Show resource name instead of ID
- [ ] Add support for Rancher Secrets (for Username/Password)
- [ ] Prefix the exposed metrics name with 'otc_ces_*'
- [ ] Token Validation
