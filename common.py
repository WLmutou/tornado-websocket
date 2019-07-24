#coding:utf-8

import sqlite3
import logging 
import argparse 
import redis 

import tornado
import mako.lookup
import mako.template

from config import sqlite_db
from config import redis_host, redis_port, redis_pass

import tornadoredis


conn = sqlite3.connect(sqlite_db)
cur  = conn.cursor()

def setup_cmd_parser():
    p = argparse.ArgumentParser(
        description='Simple WebSockets-based text chat server.')
    p.add_argument('-i', '--ip', action='store',
                   default='127.0.0.1', help='Server IP address.')
    p.add_argument('-p', '--port', action='store', type=int,
                   default=9696, help='Server Port.')
    p.add_argument('-g', '--log_file', action='store',
                   default='logsimplechat.log', help='Name of log file.')
    p.add_argument('-f', '--file_log_level', const=1, default=0, type=int, nargs="?",
                   help="0 = only warnings, 1 = info, 2 = debug. Default is 0.")
    p.add_argument('-c', '--console_log_level', const=1, default=3, type=int, nargs="?",
                   help="0 = No logging to console, 1 = only warnings, 2 = info, 3 = debug. Default is 0.")
    return p

def setup_logging(args):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)   # set maximum level for the logger,
    formatter = logging.Formatter('%(asctime)s | %(thread)d | %(message)s')
    loglevels = [0, logging.WARN, logging.INFO, logging.DEBUG]
    fll = args.file_log_level
    cll = args.console_log_level
    fh = logging.FileHandler(args.log_file, mode='a')
    fh.setLevel(loglevels[fll])
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    if cll > 0:
        sh = logging.StreamHandler()
        sh.setLevel(loglevels[cll])
        sh.setFormatter(formatter)
        logger.addHandler(sh)
    return logger

parse = setup_cmd_parser()
args = parse.parse_args()
log = setup_logging(args)

class BaseHandler(tornado.web.RequestHandler):
	pass 
    # def initialize(self):
    #     template_path = self.get_template_path()
    #     self.lookup = mako.lookup.TemplateLookup(directories=[template_path], input_encoding='utf-8', output_encoding='utf-8')
    #     #self.lookup = mako.lookup.TemplateLookup(directories=[template_path])

    # def render_string(self, template_path, **kwargs):
    #     template = self.lookup.get_template(template_path)
    #     namespace = self.get_template_namespace()
    #     namespace.update(kwargs)
    #     return template.render(**namespace)

    # def render(self, template_path, **kwargs):
    #     self.finish(self.render_string(template_path, **kwargs))


def redis_connect(redis_type="tornadoredis"):
	if redis_type == "redis":
		client = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_pass)
	elif redis_type == "tornadoredis":
		client = tornadoredis.Client(host=redis_host, port=redis_port, password=redis_pass)
	else :
		return None 
	return client


#获取用户类型
def get_usertype(username):
	try:
		username = str(username.decode())
	except:
		username = username
	sql = "select usertype from user where username = '%s' limit 1" %(username)
	print ("sql:", sql)        
	cur.execute(sql)
	usertype = cur.fetchone()
	if not usertype:
		return None
	return usertype[0]

#获取room表中的所有数据,返回[roomlist,room_owner]
def getRoomList():
	sql = "select room.roomid,room.roomname,room.created_time,room.owner_id,user.username \
			from room,user where room.owner_id == user.userid"

	cursor = conn.execute(sql)
	roomlist = list(cursor.fetchall())
	return roomlist

#根据房间id，找出房间具体信息
def getRoomInfo(roomid):
	#check roomid是否合法
	sql = "select * from room where roomid = %d" % (roomid)
	cursor = conn.execute(sql)
	ret = cursor.fetchone()
	if ret is None:
		return None
		
	#roomid is [1,Max_roomid]	
	sql = "select room.roomid,room.roomname,room.created_time,room.owner_id,user.username \
			from room,user where room.roomid = %d and room.owner_id == user.userid" %(roomid)
	cursor = conn.execute(sql)
	roominfo = list(cursor.fetchone())
	return roominfo

#example
if __name__ == "__main__":
	a = '11111'
	print(get_usertype(a))
