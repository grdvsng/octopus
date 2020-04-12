import re
import psycopg2
import json

from os        import path as osPath
from sys       import path as sysPath
from datetime  import datetime;
from peewee    import *
from importlib import import_module

baseDir = osPath.abspath(osPath.dirname(__file__))
sysPath.append(baseDir)
sysPath.append(osPath.join(*osPath.split(baseDir), ".."))

from lib import CoreHandler, module_utils

class PostgreSQLGateway(PostgresqlDatabase):
    logger           = None
    universal_models = osPath.abspath(osPath.join(baseDir, "..", "..", "models", "psql_basic_model.py"))

    def __init__(self, cfg):
        super().__init__(
            cfg['db'],
            user=cfg['user'],
            password=cfg['password'],
            host=cfg['host'],
            port=cfg['port']
        )

        self._cfg   = cfg
        self.logger = self.getLogger()

        self.connect()
        self.model_generate()
    
    def model_generate(self):
        if "use_universal_models" in self._cfg and self._cfg["use_universal_models"]:
            self.connect_model(self.universal_models)

    def connect_model(self, model_path):
        imported = module_utils.get_module(model_path)

        imported.build(self, self.logger)

    def connect(self):
        try:
            super().connect()
            
            del self._cfg['password']

            self.logger.handle("Base connected", str(json.dumps(self._cfg)), 2)
        except Exception as err:
            self.logger.handle("Base Error", type(err).__name__, 0)
    
    def getLogger(self):
        if self.logger:
            return self.logger
        else:
            params_path = osPath.abspath(osPath.join(baseDir, *osPath.split(self._cfg["logParams"] if "logParams" in self._cfg else "log_config.json")))
            log_path    = osPath.abspath(osPath.join(baseDir, *osPath.split(self._cfg["log"]       if "log"       in self._cfg else "../../logs/test.html")))
            
            return CoreHandler(params_path, log_path)


PostgreSQLGateway({
        "host":        "localhost",
        "port":        5433,
        "db":          "main",
        "user":        "postgres",
        "password":    "CPythonP@ss",
        "log":         "../../logs/test.html",
        #"model":      "../../models/models.py",
        "use_universal_models": True,
})