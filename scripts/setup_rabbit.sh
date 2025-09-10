#!/bin/bash
set -e
export RABBITMQ_DEFAULT_USER=$USER
export RABBITMQ_DEFAULT_PASS=$PASSWORD
exec /usr/local/bin/docker-entrypoint.sh rabbitmq-server