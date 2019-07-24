#coding:utf-8

import sqlite3

from config import sqlite_db 


command = """
BEGIN;
CREATE TABLE IF NOT EXISTS user(
	"userid" integer PRIMARY KEY AUTOINCREMENT,
	"username" varchar(25) NOT NULL, 
	"password" varchar(50) NOT NULL,
	"registed_time" datetime NOT NULL,
	"usertype" smallint DEFAULT 0,
	"email" varchar(30),
	"phone" varchar(20),
	"reverse1" integer DEFAULT NULL,
	"reverse2" varchar(50) DEFAULT NULL,
	UNIQUE("username") 
);

CREATE TABLE IF NOT EXISTS room(
	"roomid" integer PRIMARY KEY AUTOINCREMENT,
	"roomname" varchar(50) NOT NULL,
	"created_time" datetime NOT NULL,
    "owner_id" integer NOT NULL,
    UNIQUE("roomname")
);

CREATE TABLE IF NOT EXISTS message(
	"msgid" integer PRIMARY KEY AUTOINCREMENT,
	"roomid" integer NOT NULL,
	"username" varchar(25) NOT NULL,
	"msg" varchar(500) NOT NULL,
	"msg_type"  varchar(30) NOT NULL, 
	"created_time" datetime DEFAULT NULL,
	"reverse1" varchar(50) DEFAULT NULL
);
COMMIT;
"""

def init_db():
	con = sqlite3.connect(sqlite_db)
	cur = con.cursor()
	try:
		cur.executescript(command)
		con.commit()
	except Exception as e:
		print(e)

	cur.close()
	con.close()

if __name__ == "__main__":
	init_db()

