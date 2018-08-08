#!/bin/bash

# If environment variable RANCHER_SECRETS is set to true then replace PASSWORD value by rancher secret
if [ "$RANCHER_SECRETS" = "true" ]
then
    export PASSWORD=$(cat "/run/secrets/$PASSWORD")
fi

# Dockerize generates the configuration files and start exporter
dockerize -no-overwrite -template /app/config/app_config.tmpl:/app/config/app_config.ini  -template /app/config/log_config.tmpl:/app/config/log_config.ini python /app/main.py

