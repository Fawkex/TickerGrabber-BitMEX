#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 FawkesPan
#
#
# BitMEX WebSocket API Connection Settings.


#API Config
BASE_URL = 'wss://www.bitmex.com/realtime/websocket'

#Market
SYMBOL = "XBTUSD"

#HTTP Proxy
HTTP_PROXY_ENABLE = 0
HTTP_PROXY_HOST = '127.0.0.1'
HTTP_PROXY_PORT = 8080

#Storage
STORAGE_METHOD = 'redis'              # redis or csv

REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_DB = '0'

CSV_FILENAME = 'BitMEX.csv'

def get_config():
    config = {}

    config['BASE_URL'] = BASE_URL

    config['SYMBOL'] = SYMBOL

    config['HTTP_PROXY_ENABLE'] = HTTP_PROXY_ENABLE
    config['HTTP_PROXY_HOST'] = HTTP_PROXY_HOST
    config['HTTP_PROXY_PORT'] = HTTP_PROXY_PORT

    config['STORAGE_METHOD'] = STORAGE_METHOD

    config['REDIS_HOST'] = REDIS_HOST
    config['REDIS_PORT'] = REDIS_PORT
    config['REDIS_DB'] = REDIS_DB

    config['CSV_FILENAME'] = CSV_FILENAME

    return config
