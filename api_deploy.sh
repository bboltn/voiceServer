#!/bin/bash

cd /srv/sites/api
git pull origin master
service uwsgi restart
redis-cli flushdb

