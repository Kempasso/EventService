#!/bin/bash
set -e

export MONGO_INITDB_ROOT_USERNAME=$MONGO_USER
export MONGO_INITDB_ROOT_PASSWORD=$MONGO_PASSWORD
export MONGO_INITDB_DATABASE=$MONGO_DB
exec /usr/local/bin/docker-entrypoint.sh mongod