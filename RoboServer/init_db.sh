#!/bin/bash
set -e

psql --dbname postgres --username=postgres --no-password --command="CREATE DATABASE robo_friend WITH OWNER postgres"

psql --dbname robo_friend --username=postgres --no-password -f /docker-entrypoint-initdb.d/tables.sql