#!/bin/bash

# little script to restore airbyte on EC2 instance with docker/git
# author: ccavallo@blueroange.digital
# 
#
#variables
GH_REPO="https://github.com/Asmartment/airbyte-restore"
OCTAVIA="docker run -i --rm -v .:/home/octavia-project --network host airbyte/octavia-cli:0.40.32"
#install docker

apt install docker-ce docker-compose subversion -y
#install airbyte

git clone $GH_REPO
cd airbyte-restore/airbyte-dev
docker compose up -d

cd airbyte-configuration

#parser buggy get error with geography and non_breaking_changes_preference

find . -name configuration.yaml -exec perl -i -p -e "s/geography:/#geography:/g" {} \
find . -name configuration.yaml -exec perl -i -p -e "s/non_breaking_changes_preference/#non_breaking_changes_preference/g" {} \;

sleep 30

# apply backup 
$OCTAVIA --airbyte-url http://localhost:8000 apply

