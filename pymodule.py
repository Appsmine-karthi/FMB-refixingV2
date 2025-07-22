import json
import sys
import pydep.main as main
def process(name):
    data = json.loads(name)
    func_name = data["mod"]
    args = data.get("arg", [])
    kwargs = data.get("kwargs", {})
    func = getattr(main, func_name)
    return func(*args, **kwargs)
