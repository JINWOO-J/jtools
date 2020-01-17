#!/bin/bash
PATH=$PATH:/usr/local/bin
if [[ ! -d "data" ]];then
    echo "[ERROR] can not found data directory, Must run in a directory with Docker-compose.yml"
    exit 127;
fi

docker pull jinwoo/jtools
docker run -it --rm -v ${PWD}/data:/data jinwoo/jtools sendme_log.py -d /data --upload-type multi $@
