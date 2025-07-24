import json
import sys
import os
import multiprocessing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pydep'))


import pydep.main as main

def process(name):

    def _call_func(func_name, args, kwargs, queue):
        import pydep.main as main
        func = getattr(main, func_name)
        result = func(*args, **kwargs)
        queue.put(result)

    data = json.loads(name)
    func_name = data["mod"]
    args = data.get("arg", [])
    kwargs = data.get("kwargs", {})

    queue = multiprocessing.Queue()
    p = multiprocessing.Process(target=_call_func, args=(func_name, args, kwargs, queue))
    p.start()
    p.join()
    result = queue.get()
    return result
