#coding:utf-8

import tornado.web
import tornado.ioloop
import tornado.httpserver
import tornado.options
import json
import tornado.web
import tornado.gen
import tornadoredis
from tornado.escape import json_encode

import os.path
import sqlite3
import datetime
import time
import common


from tornado.options import define, options

from config import redis_host, redis_port, redis_pass 
from config import sqlite_db 
from common import BaseHandler


conn = sqlite3.connect(sqlite_db)
cur  = conn.cursor()


c = tornadoredis.Client(host=redis_host, port=redis_port, password=redis_pass)
c.connect()


def dict_factory(cursor, row):  
    d = {}  
    for idx, col in enumerate(cursor.description):  
        d[col[0]] = row[idx]  
    return d  

conn.row_factory = dict_factory




#显示所有聊天室的类
class ChatRoomHandler(BaseHandler):
	def get_current_user(self):
		return self.get_secure_cookie("username")

	def get(self):
		cookie_user = self.get_secure_cookie("username")
		roomlist = common.getRoomList()
		if cookie_user:
			usertype = common.get_usertype(cookie_user)
			self.render('chatroom.html', cookieUser=cookie_user, usertype = usertype,Error=False,
						roomlist=roomlist)
		else:
			self.render('login.html', cookieUser=None, Error = False)
			
	def post(self):
		return

#创建聊天室
class CreateRoomHandler(BaseHandler):

	#检查roomname是否被使用，未被使用返回False
	def check_is_userd(self,roomname):
		sql = "select roomname from room where roomname = '%s' " %(roomname)
		cur.execute(sql)
		if cur.fetchall():
			return True;
		return False;

	def get(self):
		cookie_user = self.get_secure_cookie("username")
		if cookie_user:
			usertype = common.get_usertype(cookie_user)
			self.render('createroom.html', cookieUser=cookie_user, usertype = usertype,Error=False)
		else:
			self.render('login.html', cookieUser=None, Error = False)
	#创建聊天室
	def post(self):
		roomname = self.get_argument('roomname')
		username = self.get_secure_cookie('username')
		try:
			username = username.decode()
		except NameError:
			username = username

		#roomname被使用过
		if self.check_is_userd(roomname):
			usertype = common.get_usertype(username)
			self.render('createroom.html', cookieUser=username, usertype = usertype, Error=True)
			return

		sql = "select userid from user where username = '%s' " % (username)
		cursor = conn.execute(sql)
		userid = 0

		rows = cursor.fetchone()
		# print (rows )
		userid = rows["userid"]
		# for row in cursor:
			# userid = row[0]
		#
		if userid <=0:
			self.redirect("/login")
			return 
		#创建
		sql = "insert into room (roomname, created_time, owner_id) \
				values('%s', datetime('now'), %d)" %(roomname, userid)
		conn.execute(sql)
		conn.commit()
		self.redirect("/chatroom")
#聊天
class ChatHandler(BaseHandler):
	def initialize(self, room_handler):
		self.room_handler = room_handler

	def get(self, action=None):	
		uri_list = self.request.uri.split('/')
		roomid = int(uri_list[-1])

		self.set_secure_cookie("roomid", str(roomid),1)
		cookie_user = self.get_secure_cookie("username")
		try:
			cookie_user = cookie_user.decode()
		except :
			cookie_user = cookie_user

		client_id = self.room_handler.add_room(roomid, cookie_user)
		self.set_cookie("ftc_cid", str(client_id))

		if cookie_user:
			usertype = common.get_usertype(cookie_user)
			roominfo = common.getRoomInfo(roomid)
			if roominfo is None:
				#跳转404
				self.render("404err.html")
			#成功合法跳转某聊天房
			else:
				sql = "select username,msg,created_time from message where roomid = %d order by msgid \
						desc limit 100" % (roomid)
				cursor = conn.execute(sql)
				#最近50条聊天记录
				msginfoList = list(cursor.fetchall())
				msginfoList.reverse()
				for msg in msginfoList:
					if msg.get("username") == cookie_user:
						msg["userself"] = True
				# render
				self.render('chat.html', cookieUser=cookie_user, usertype = usertype,
							roominfo=roominfo, msginfo=msginfoList)
		else:
			self.render('login.html', cookieUser=None, Error = False)

	@tornado.web.asynchronous
	def post(self):
		username = self.get_secure_cookie("username")
		username = username.decode()
		msg = self.get_argument("msg")
		#print '[get msg ok!] msg: ',msg
		data = json_encode({'name':username, 'msg':msg})
		roomchannel = self.get_secure_cookie('roomid')
		roomchannel = roomchannel.decode()
		#持久化
		sql = "insert into message(roomid,username,msg,created_time)\
			   values(%d,'%s','%s',datetime('now'))" % (int(roomchannel),username,msg)
		conn.execute(sql)
		conn.commit()

		#收到将消息publish到Redis
		#print data
		c.publish(roomchannel, data)
		
		self.write(json_encode({'result':True}))
		self.finish()
