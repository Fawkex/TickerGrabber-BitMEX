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

config = {}
config = apiconfig.get_config()

SYMBOL = config['SYMBOL']
fairPrice = 111111
vals = {}

if config['STORAGE_METHOD'] == 'redis':
    import redis
    r = redis.Redis(host=config['REDIS_HOST'],port=config['REDIS_PORT'],db=config['REDIS_DB'])
elif config['STORAGE_METHOD'] == 'csv':
    f = open(config['CSV_FILENAME'],"a")
elif config['STORAGE_METHOD'] == 'mysql':
    try:
        import MySQLdb
    except:
        import pymysql as MySQLdb
    if config['MYSQL_WARNINGS_SWITCH'] == 0:
        from warnings import filterwarnings
        filterwarnings('ignore', category = MySQLdb.Warning)
    s = MySQLdb.connect(host=config['MYSQL_HOST'],
                        port=config['MYSQL_PORT'],
                        user=config['MYSQL_USER'],
                        passwd=config['MYSQL_PASS'],
                        db=config['MYSQL_DB'])
    s.ping(True)

def subscribe(ws):
    def run(*args):
        ws.send('{"op": "subscribe", "args": ["trade:%s"]}' % SYMBOL)
        ws.send('{"op": "subscribe", "args": ["instrument:%s"]}' % SYMBOL)
        while True:
            ws.send('ping')
            time.sleep(5)

    Thread(target=run).start()

def WriteREDIS(ws,message):
    global fairPrice
    p = r.pipeline()
    if 'table' in message and 'trade' in message and fairPrice != 111111:
        data = json.loads(message)['data']
        multi = 0
        for tickers in data:
            if tickers['timestamp'] == '':
                return
            date = tickers['timestamp'].replace('-','').replace('T','').replace(':','').replace(".",'').replace('Z',"%04d" % multi)
            multi = multi + 1
            if 'Minus' in tickers['tickDirection']:
                side = 'SELL'
                change = -1
            else:
                side = 'BUY'
                change = 1
            if 'Zero' in tickers['tickDirection']:
                change = 0
            vals['symbol'] = SYMBOL
            vals['side'] = side
            vals['price'] = tickers['price']
            vals['fairPrice'] = fairPrice
            vals['size'] = tickers['homeNotional']
            vals['value'] = tickers['foreignNotional']
            vals['change'] = change
            p.hmset("timestamp:"+date,vals)
            p.execute()
        

    if 'table' in message and 'fairPrice' in message:
        fairPrice = json.loads(message)['data'][0]['fairPrice']
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + " Current " + SYMBOL + " fairPrice: " + str(fairPrice))
            
    if 'pong' in message:
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + " Pong.")

def WriteMYSQL(ws,message):
    global fairPrice
    q = s.cursor()
    if 'table' in message and 'trade' in message and fairPrice != 111111:
        data = json.loads(message)['data']
        multi = 0
        tickers_ = ""
        for tickers in data:
            if tickers['timestamp'] == '':
                return
            date = tickers['timestamp'].replace('-','').replace('T','').replace(':','').replace(".",'').replace('Z',"%04d" % multi)
            multi = multi + 1
            if 'Minus' in tickers['tickDirection']:
                side = 'SELL'
                change = -1
            else:
                side = 'BUY'
                change = 1
            if 'Zero' in tickers['tickDirection']:
                change = 0
            if multi == 1:
                tickers_ = "(%s,\"%s\",\"%s\",%.2f,%.2f,%.8f,%d,%d)" % (date,SYMBOL,side,tickers['price'],fairPrice,tickers['homeNotional'],tickers['foreignNotional'],change)
            else:
                tickers_ = "%s,(%s,\"%s\",\"%s\",%.2f,%.2f,%.8f,%d,%d)" % (tickers_,date,SYMBOL,side,tickers['price'],fairPrice,tickers['homeNotional'],tickers['foreignNotional'],change)
        
        cmds = "INSERT IGNORE INTO bitmex (`Timestamp`,`Symbol`,`Side`,`Price`,`fairPrice`,`Size`,`Value`,`Change`) VALUES %s;" % tickers_

        try:
            q.execute(cmds)
            s.commit()
        except:
            s.rollback()

        q.close()

    if 'table' in message and 'fairPrice' in message:
        fairPrice = json.loads(message)['data'][0]['fairPrice']
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + " Current " + SYMBOL + " fairPrice: " + str(fairPrice))
            
    if 'pong' in message:
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + " Pong.")

def WriteCSV(ws,message):
    global fairPrice
    if 'table' in message and 'trade' in message and fairPrice != 111111:
        data = json.loads(message)['data']
        multi = 0
        for tickers in data:
            if tickers['timestamp'] == '':
                return
            date = tickers['timestamp'].replace('-','').replace('T','').replace(':','').replace(".",'').replace('Z',"%04d" % multi)
            multi = multi + 1
            if 'Minus' in tickers['tickDirection']:
                side = 'SELL'
                change = -1
            else:
                side = 'BUY'
                change = 1
            if 'Zero' in tickers['tickDirection']:
                change = 0
            price = tickers['price']
            size = tickers['homeNotional']
            value = tickers['foreignNotional']
            f.write("{},{},{},{},{},{},{},{}".format(date,SYMBOL,side,price,fairPrice,size,value,change))
            f.write("\n")
    
        f.flush()

    if 'table' in message and 'fairPrice' in message:
        fairPrice = json.loads(message)['data'][0]['fairPrice']
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + " Current " + SYMBOL + " fairPrice: " + str(fairPrice))

    if 'pong' in message:
        print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())) + " Pong.")

def on_error(ws,error):
    print(error)

def closing(ws):
    print("Shuting Down...")
    if config['STORAGE_METHOD'] == 'mysql':
        s.close()
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
    elif METHOD == 'mysql':
        ws = websocket.WebSocketApp(URL,
                                    on_message=WriteMYSQL,
                                    on_error=on_error,
                                    on_close=closing)
    else:
        print("Unsupported Storage Method. Exiting...")

        exit()
    
    ws.on_open = subscribe
    ws.run_forever()

if __name__ == '__main__':
    main()
