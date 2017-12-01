#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 FawkesPan
#
#

import time
import ssl
import sys
import code
import json
from threading import Thread

import apiconfig

import six
from six.moves.urllib.parse import urlparse

import websocket

import string

try:
    import readline
except ImportError:
    pass

SYMBOL = 'XBTUSD'
fairPrice = 111111
vals = {}

config = {}
config = apiconfig.get_config()

if config['STORAGE_METHOD'] == 'redis':
    import redis
    r = redis.Redis(host=config['REDIS_HOST'],port=config['REDIS_PORT'],db=config['REDIS_DB'])
elif config['STORAGE_METHOD'] == 'csv':
    f = open(config['CSV_FILENAME'],"a")

def subscribe(ws):
    def run(*args):
        ws.send('{"op": "subscribe", "args": ["trade:%s"]}' % SYMBOL)
        ws.send('{"op": "subscribe", "args": ["instrument:%s"]}' % SYMBOL)
        while True:
            ws.send('ping')
            time.sleep(5)

    Thread(target=run).start()

def WriteREDIS(ws,message):
    p = r.pipeline()
    if 'table' in message and 'trade' in message and markPrice != 111111:
        data = json.loads(message)['data']
        multi = 0
        for tickers in data:
            if tickers['timestamp'] == '':
                return
            date = tickers['timestamp'].replace('-','').replace('T','').replace(':','').replace(".",'').replace('Z',"%04d" % multi)
            multi = multi + 1
            if tickers['tickDirection'] == 'MinusTick':
                side = 'SELL'
                change = -1
            elif tickers['tickDirection'] == 'ZeroMinusTick':
                side = 'SELL'
                change = 0
            elif tickers['tickDirection'] == 'PlusTick':
                side = 'BUY'
                change = 1
            elif tickers['tickDirection'] == 'ZeroPlusTick':
                side = 'BUY'
                change = 0
            price = tickers['price']
            size = tickers['homeNotional']
            value = tickers['foreignNotional']
            vals['symbol'] = SYMBOL
            vals['side'] = side
            vals['price'] = price
            vals['fairPrice'] = fairPrice
            vals['size'] = size
            vals['value'] = value
            vals['change'] = change
            p.hmset("timestamp:"+date,vals)
        
        p.execute()

    if 'table' in message and 'instrument' in message:
        global fairPrice
        fairPrice = json.loads(message)['data']['fairPrice']
            
    if 'pong' in message:
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + "  To the moon.")

def WriteCSV(ws,message):
    if 'table' in message and 'trade' in message and markPrice != 111111:
        data = json.loads(message)['data']
        multi = 0
        for tickers in data:
            if tickers['timestamp'] == '':
                return
            date = tickers['timestamp'].replace('-','').replace('T','').replace(':','').replace(".",'').replace('Z',"%04d" % multi)
            multi = multi + 1
            if tickers['tickDirection'] == 'MinusTick':
                side = 'SELL'
                change = -1
            elif tickers['tickDirection'] == 'ZeroMinusTick':
                side = 'SELL'
                change = 0
            elif tickers['tickDirection'] == 'PlusTick':
                side = 'BUY'
                change = 1
            elif tickers['tickDirection'] == 'ZeroPlusTick':
                side = 'BUY'
                change = 0
            price = tickers['price']
            size = tickers['homeNotional']
            value = tickers['foreignNotional']
            f.write("{},{},{},{},{},{},{},{}".format(date,SYMBOL,side,price,fairPrice,size,value,change))
            f.write("\n")
    
        f.flush()

    if 'table' in message and 'instrument' in message:
        global fairPrice
        fairPrice = json.loads(message)['data']['fairPrice']

    if 'pong' in message:
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + "  To the moon.")

def on_error(ws,error):
    print(error)

def closing(ws):
    print("Shuting Down...")
    ws.close()

def main():
    options = {}

    websocket.enableTrace(True)

    if config['HTTP_PROXY_ENABLE']:
        options['http_proxy_host'] = config['HTTP_PROXY_HOST']
        options['http_proxy_port'] = config['HTTP_PROXY_PORT']

    URL = config['BASE_URL']
    METHOD = apiconfig.get_config()['STORAGE_METHOD']

    if METHOD == 'redis':
        ws = websocket.WebSocketApp(URL,
                                    on_message=WriteREDIS,
                                    on_error=on_error,
                                    on_close=closing)
    elif METHOD == 'csv':
        ws = websocket.WebSocketApp(URL,
                                    on_message=WriteCSV,
                                    on_error=on_error,
                                    on_close=closing)
    else:
        print("Unsupported Storage Method. Exiting...")

        exit()
    
    ws.on_open = subscribe
    ws.run_forever()

if __name__ == '__main__':
    main()
