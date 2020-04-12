import re
import sys

from importlib import util  as import_util
from os.path   import split as os_path_split


def get_module(path, module_name=False):
    if not module_name:
        module_name = re.sub(r"[\.][^\.]+$", "", os_path_split(path)[-1])
    
    spec   = import_util.spec_from_file_location(module_name, path)
    module = import_util.module_from_spec(spec)
    sys.modules[spec.name] = module 
    spec.loader.exec_module(module)

    return module