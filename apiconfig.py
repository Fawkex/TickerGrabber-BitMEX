# BitMEX WebSocket API Connection Settings.
#
# Copyright 2017-2018 FawkesPan
#
#

[API CONFIG]
BASE_URL = 'wss://www.bitmex.com/realtime/websocket'

[MARKET]
SYMBOL = "XBTUSD"

[HTTP PROXY]
ENABLE = 0
HOST = '127.0.0.1'
PORT = 8080

[Storage]
METHOD = 'mysql'                     # csv/mysql(recommanded)/redis

[REDIS]
HOST = '127.0.0.1'
PORT = 6379
DB = '0'

[MYSQL]
HOST = 'localhost'
PORT = 3306
USER = 'bitmex'
PASS = 'bitmex'
DB = 'bitmex'
WARNINGS_SWITCH = 0                   # Set 0 to disable MySQL Warnings.

[CSV]
FILENAME = 'BitMEX.csv'