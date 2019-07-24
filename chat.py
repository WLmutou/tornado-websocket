#!/usr/bin/env python
# encoding:utf-8

import tornado 
import json 
import re
import uuid 
import logging 
import time 
import tornadoredis 
from tornado.websocket import WebSocketHandler

from config import redis_host, redis_port, redis_pass
from common import redis_connect
from common import log 
from common import conn 

MAX_ROOMS = 100
MAX_USERS_PER_ROOM = 3 

singleclient = redis_connect()
singleclient.connect()

class RoomHandler(object):
    def __init__(self):
        self.redis_cli = redis_connect("redis")
    
    def add_room(self, room, nick):
        room_info = self.redis_cli.smembers("members-rooms")
        if not room in room_info:
            if len(room_info) > MAX_ROOMS:
                log.error("MAX_ROOMS_REACHED")
                return -1 
            self.redis_cli.sadd("members-rooms", room)
            log.debug("ADD_ROOM - ROOM_NAME: %s " % room)

        log.info("room name %s" % (room_info))
        room_user = self.redis_cli.smembers("members-%s-users"  % (room))

        if room in room_info:
            if len(room_user) >= MAX_USERS_PER_ROOM:
                log.error("MAX_USERS_PER_ROOM_PEACHED")
                return -2 

        print ("add room:", room, nick)

        roomvalid = re.match(r'[\w-]+$', str(room))
        nickvalid = re.match(r'[\w-]+$', str(nick))
        if roomvalid == None:
            log.error("INVALID_ROOMT_NAME - ROOM: %s " % (room,))
            return -3 
        if nickvalid == None:
            return -4 
            log.error("INVALID_NICK_NAME - NICK:%s" % (nick,))
        client_id = uuid.uuid4().int  # client id 
        self.redis_cli.set("%s-%s" % (client_id, "room"), room)

        c = 1 
        name = nick 
        nicks = self.nicks_in_room(room)
        while  True:
            if name in nicks:
                name = nick + str(c)
            else:
                break 
            c += 1 
            
        self.redis_cli.set("%s-%s" % (client_id, "nick"), name)
        self.redis_cli.sadd("members-%s-users" % (room) , name)
        return client_id

    def nicks_in_room(self, room):
        return self.redis_cli.smembers("members-%s-users" % (room))



        
class NewChatStatus(WebSocketHandler):
    '''
        websocket， 记录客户端连接，删除客户端连接，接收最新消息
    '''
    def __init__(self, *args, **kwargs):
        super(NewChatStatus, self).__init__(*args, **kwargs)
        self.nclient = redis_connect("redis")
        self.client_id = int(self.get_cookie("ftc_cid", 0))
        self.room = (self.nclient.get("%s-%s" % (self.client_id, "room"))).decode()
        self.nick = (self.nclient.get("%s-%s" % (self.client_id, "nick"))).decode()
        self.listen()

    @tornado.gen.engine
    def listen(self):
        self.client = redis_connect()
        self.client.connect()
        self.new_message_send = False 
        yield tornado.gen.Task(self.client.subscribe, self.room)
        self.subscribe = True 
        self.client.listen(self.on_message_publish)
        logging.info("new user connected to chat room " + str(self.room))
        self.post_msg(self.client_id, msg_type="join")
        pass 

    def on_message_publish(self, message):
        logging.debug("===message===[%s]====" % (str(message)))
        if message.kind == "message":
            data = json.loads(message.body)
            self.write_message(str(message.body))

    def on_message(self, message):
        # print ("on message:", message, self.client_id)
        log.debug("====message====[%s]===" % (str(message)))
        data = json.loads(message)
        self.post_msg(self.client_id, msg_type=data["msgtype"], message=data["payload"])

        ### 持久化
        sql = "insert into message(roomid, username, msg, msg_type, created_time) \
         values('%s', '%s', '%s', '%s', datetime('now'))" % (str(self.room), data["username"], data["payload"], data["msgtype"])
        try:
            conn.execute(sql)
            conn.commit()
        except Exception as e:
            print (e)
            log.error(e)

    def post_msg(self, client_id, msg_type="join", message=None):
        data = dict(time="%10.6f" % time.time(), msg_type=msg_type)
        data["username"] = self.nick 
        if msg_type.lower() == "join":
            data["payload"] = "joined the chat room"
        elif msg_type.lower() == "leave":
            data["payload"] =  "left the chat room"
        elif msg_type.lower() == "nick_list":
            data["payload"] = self.nclient.smembers("members-%s-users" % (room))
        elif msg_type.lower() == "text":
            data["payload"] = message 
        pmessage = json.dumps(data)
        singleclient.rpush(self.room, pmessage)
        singleclient.publish(self.room, pmessage)

    def on_close(self):
        logging.info("socket closed, cleaning up resources now")
        if self.client.subscribed:
            self.client.unsubscribe(self.room)
            self.post_msg(self.client, msg_type="leave")
            self.client.disconnect()



            
