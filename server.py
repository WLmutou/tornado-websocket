#coding:utf-8

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import os.path
import sqlite3
import datetime
import time

from chatroom import ChatRoomHandler, CreateRoomHandler, ChatHandler
from login 	  import LoginHandler, LogoutHandler
from register import RegisterHandler
from user 	  import ModifyHandler, AdminHandler
from chat      import NewChatStatus,  RoomHandler  
from tornado.options import define, options
from common      import redis_connect
from init_sqlite import init_db 

define("port", default=8000, help="run on given port", type=int)

class Application(tornado.web.Application):
	def __init__(self):
		self.room_handler = RoomHandler()
		self.client = redis_connect()
		handlers = [(r'/login', LoginHandler),
					(r'/',LoginHandler),
					(r'/logout', LogoutHandler),
					(r'/register', RegisterHandler),
					(r'/chatroom', ChatRoomHandler),
					(r'/modify', ModifyHandler),
					(r'/admin', AdminHandler),
					(r'/create', CreateRoomHandler),
					(r'/room/\d*', ChatHandler, {"room_handler": self.room_handler}),
					(r'/chat', NewChatStatus),
					]
		settings = dict(
					cookie_secret =
					"bZJc2sWbQLKos6GkHn/VB9oXwQt8S0R0kRvJ5/xJ89E=",
					template_path =
					os.path.join(os.path.dirname(__file__), "templates"),
					static_path =
					os.path.join(os.path.dirname(__file__), "static"),
					)
		tornado.web.Application.__init__(self, handlers, **settings)

def init_server():
	init_db()
	pass 

if __name__ == "__main__":
	## 初始化做点事情
	init_server()

	## 
	tornado.options.parse_command_line()
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	print ("server run on:", options.port)
	tornado.options.parse_command_line()
	tornado.ioloop.IOLoop.instance().start()
