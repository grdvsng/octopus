from flask   import Flask
from os.path import dirname
from sys     import path as sysPath

sysPath.append(dirname(__file__))
from lib            import CoreHandler, osPath, getJsonContentFromFile, RedisGateway, PostgreSQLGateway
from requestHandler import RequestHandler


class MiniBase(object):
	baseDir = osPath.dirname(__file__)
	_config = {}
	flask   = None

	def __init__(self, serverCfgPAth, logCfgPath=False):
		self._configPAth   = osPath.join(self.baseDir, *osPath.split(serverCfgPAth))
		self.logParams     = osPath.abspath(osPath.join(self.baseDir, *osPath.split(logCfgPath) if logCfgPath else "lib/log_config.json"))
		self.handler       = CoreHandler(self.logParams)
		self.jsonFiles     = [{
			"att": "_config",
			"path": self._configPAth
		}]

		self._initConfig()
		self._connectToBase()

	def _initConfig(self):
		self._setAttrsByJsonFiles()
		self.initContentConfig()
		self.initBasicConfig()


	def _getBaseClass(self, clsName):
		if clsName == 'redis':
			return RedisGateway
		elif clsName == "postgresql":
			return PostgreSQLGateway
		else:
			self.handler("Base Error", "Base '%s' not support" % clsName, 0)

	def _connectToBase(self):
		if not self._config["base"]:
			self.handler("Server error", "Base config not found...", 1)
		else:
			try:
				base_class                        = self._getBaseClass(self._config["base"]["type"])
				self._config["base"]["logParams"] = self.logParamsPath
				self.BaseConnector                = base_class(self._config["base"])

				self.handler("Base connected!", "", 2)

			except:
				self.handler("Base server not availed!", "Critical error.", 0)

	def _setAttrsByJsonFiles(self):
		for item in self.jsonFiles:
			path    = item["path"]
			attName = item["att"]

			if not osPath.exists(path):
				self.handler("Main path not exists", "File: %s" % path, 0)
			else:
				self._setAttFromJsonFile(attName, path)

	def _setAttFromJsonFile(self, attName, jsonPath):
			try:
				self.__setattr__(attName, getJsonContentFromFile(jsonPath))
				self.handler("Attribute connected!", "Attribute: %s" % attName, 2)

			except:
				self.handler("Error on file parse.", "File: %s" % jsonPath, 0)

	def start(self):
		self.handler("Server loading", "Server start running!", 2)
		self.run(**self._config["connection"])

	def initContentConfig(self):

		for k, p in self._config["files"].items():
			absPath = osPath.join(self.baseDir, *osPath.split(p))

			if not osPath.exists(absPath):
				self.handler("Template file not exists.", "File: %s" % absPath, 1)

			else:
				self.__setattr__(k, absPath)
				self.handler("Template file connected.", "File: %s" % absPath, 2)

	def initBasicConfig(self):
		self.flask  = Flask(__name__, template_folder=self.template_folder, static_folder=self.static_folder)
		self.config = self.flask.config
		self.run    = self.flask.run

		RequestHandler(self)