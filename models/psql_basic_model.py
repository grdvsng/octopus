import sys, inspect

from peewee   import *
from datetime import datetime
 

class Users:
    id         = PrimaryKeyField(null=False)
    #avatar     = BinaryUUIDField()
    login      = CharField(max_length=100, null=False)
    password   = CharField(max_length=100, null=False)
    email      = CharField(max_length=200, null=False)
    active     = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.now())
    updated_at = DateTimeField(default=datetime.now())
    aboutme    = TextField()
    
    class Meta:
        db_table = "Users"
        order_by = ('login',)


def getBasicModel(basic_cls, dbhandle, clsName=None):
    global dbhandle_, _cls, basic
    
    clsName  = clsName if not clsName is None else basic_cls.__class__.__name__
    dbhandle_ = dbhandle
    basic     = basic_cls

    exec("\rglobal _cls, basic\ndef cls():\n\tclass {0}(Model, basic): \n\t\tclass Meta:\n\t\t\tdatabase = dbhandle_\n\treturn {0}\n_cls = cls".format(clsName))
    
    return _cls()

def build(dbhandle, logger=None):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        
        if inspect.isclass(obj) and str(obj).find(__name__) != -1: 
            real_object = getBasicModel(obj, dbhandle, name)

            try:
                title = "Model connected"
                msg   = "{{'name': '{0}', 'status': 'connected'}}".format(name)
                
                real_object.create_table()
                logger.handle(title, msg, 2) if logger else print(title + msg)

            except Exception as error:
                title = "Model inicialization fail"
                msg   = "{{'name': '{0}', 'error': '{1}'}}".format(name, error)

                logger.handle(title, msg, 1) if logger else print(title + msg)