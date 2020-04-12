import re
import json

from redis import *


class RedisGateway(Redis):
	"""
	class RedisGateway

	class connector to Redis base

	return codes:
		0  - ok
		-1 - table not found
		-2 - key allready exist
		-3 - key not exist
		-4 - table not created
		-5 - table allready exist
		-6 - method for query not found
		-7 - bad query

	"""

	def __init__(self, config):
		self.host = config["host"] if "host" in config else 'localhost'
		self.port = config["port"] if "port" in config else 6379
		self.db   = config["db"]   if "db"   in config else 0

		super().__init__(host=self.host, port=self.port, db=self.db)
		self._checkConnection()
		self.disabledNotUsingMethod()

	def _checkConnection(self):
		self.get("1")

	def _push(self, tableName, params, createTable=False):
		for item in params:
			resp = self.pushInTable(tableName, item["key"], item["val"], createTable)

			if resp != 0:
				return resp

		return 0

	def query(self, tables, method="select", params="key -like '*'", createTable=False):
		if method == "select":
			return self._select(tables, params)

		elif method == "push":
			return self._push(tables, params, createTable)

		else:
			return -6

	def _checkQueryParams(self, filters):

		for params in filters:
			if (not params[0] in ["key", "val"]):
				return -7
			elif (not params[1] in ["==", ">=", "<=", "!=", "like"]):
				return -7

		return True

	def _connectOperator(self, oldResult, newResult, operator):

		if oldResult == None:
			return newResult
		else:
			if operator == ' or ':
				return oldResult or newResult
			else:
				return oldResult and newResult

	def _compileQuery(self, filters, key, val):
		_filters  = re.split(r" or | and ", filters)
		operators = re.findall(r" or | and ", filters, re.I)
		result    = None
		step      = -1

		for params in _filters:
			params = params.split(" ")
			compar = key if params[0] == "key" else val
			onComp = re.sub(r"^[\'\"]|[\'\"]$", "", params[2])
			op     = None if step < 0 else operators[0]

			if (params[1] == "=="):    result = self._connectOperator(result, compar == onComp, op)
			if (params[1] == ">="):    result = self._connectOperator(result, compar >= onComp, op)
			if (params[1] == "<="):    result = self._connectOperator(result, compar <= onComp, op)
			if (params[1] == "!="):    result = self._connectOperator(result, compar != onComp, op)
			if (params[1] == "in"):    result = self._connectOperator(result, compar in json.loads(params[2]), op)
			if (params[1] == "notIn"): result = self._connectOperator(result, not compar in json.loads(params[2]), op)
			if (params[1] == "like"):
				result = self._connectOperator(result, len(self._onRegExp(re.findall, onComp, compar)) > 0, op)

			step += 1

		return result

	def _onRegExp(self, method, rp, txt):
		try:
			eq = method(r"%s" % rp, txt, re.IGNORECASE)

			return eq
		except:
			return -7

	def _parseTableByQuery(self, table, param):
		row      = []
		_filters = re.split(r" or | and ", param)

		if not self._checkQueryParams(_filters):
			return -7

		for key, val in table.items():
			if (self._compileQuery(param, key, val)):
				row.append([key, val])

		return row if len(row) > 0 else 0

	def _select(self, tables, where):
		for tableName in tables:
			table = self.getTable(tableName)

			if (table == -1): return -1

			curTable = self._parseTableByQuery(table, where);

			if (curTable == -7): return -7

		return curTable

	def disabledNotUsingMethod(self):
		self.get             = None
		self.set             = None
		self.register_script = None

	def _runWithPipeline(self, inquiries):
		_pipe = self.pipeline()

		for inq in inquiries:
			exec('_pipe.%s(*inq["params"])' % inq["method"])

		return _pipe.execute()

	def getTable(self, tableName):
		table = self.hgetall(tableName)

		if (len(table) == 0):
			return -1
		else:
			return { k.decode('ascii'): v.decode('ascii') for k,v in table.items() } 

	def pushInTable(self, tableName, key, value, createTable=False):
		table = self.getTable(tableName)

		if table != -1 or createTable:
			if isinstance(table, dict) and key in table:
				return -2
			else:
				self.hset(tableName, key, value)
				self.save()

				return 0

		else:
			return -1

	def getFromTable(self, tableName, key):
		table = self.getTable(tableName)

		if table != -1:
			if not key in tableName:
				return -3
			else:
				return tableName[key]
		else:
			return -1

	def createTable(self, tableName, data={"test": "0"}):

		if self.getTable(tableName) == -1:
			self.hmset(tableName, data)

			if self.getTable(tableName) == -1:
				return -4
			else:
				self.save()

				return 0

		else:
			return -5

	def _removeTable(self, tableName):
		table = self.getTable(tableName)

		for key in table.keys():
			self.hdel(tableName, key)

	def removeFromTable(self, tableName, key):
		table = self.getTable(tableName)

		if table == -1:
			return -1

		else:
			self.hdel(tableName, key)

			if self.getFromTable(tableName, key) != -3:
				return -2
			else:
				self.save()

				return 0

	def removeTable(self, tableName):
		if self.getTable(tableName) == -1:
			return -1

		else:
			self._removeTable(tableName)

			if self.getTable(tableName) == -1:
				self.save()

				return 0
			else:
				return -5