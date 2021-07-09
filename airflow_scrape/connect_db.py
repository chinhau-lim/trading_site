'''
	This code is developed by Chin Hau Lim.

	Goal: 
	    1. Connect to Database.
	    2. Get Specific Table Columns.
        3. Get Connection Engine.

'''

import os
import sqlite3
from sqlite3 import Error
from sqlalchemy import create_engine


class Database_Connection:

	def __init__(self):
		self.DATABASE_FILENAME = 'database/trading_db.sqlite3'

	def connect_to_db(self):
		'''Establish a connection to database.'''
		conn = None
		try:
			conn = sqlite3.connect(self.DATABASE_FILENAME)
			return conn
		except Error as err:
			print("Error : ", err)
			if conn is not None:
				conn.close()
			return None

	def get_table_columns(self, table_name):
		'''Return the table columns.'''
		
		conn = self.connect_to_db()
		column_names = list()
		if conn is not None:
			cc = conn.cursor()
			table_column_names = 'PRAGMA table_info(' + table_name + ');'
			cc.execute(table_column_names)
			table_column_names = cc.fetchall()
			column_names = list()
			for name in table_column_names:
				column_names.append(name[1])
		return column_names

	def get_conn_engine(self):

		engine = create_engine('sqlite:///' + self.DATABASE_FILENAME, echo=False)
		return engine