import json
import sys
import os
import multiprocessing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pydep'))

from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
app = FastAPI()

@app.post("/process")
async def process_generic(request: Request):
    try:
        data: Dict[str, Any] = await request.json()
        rtn = process(data["mod"], data["arg"])
        processed = {
            "received": rtn
        }

        return JSONResponse(content=processed)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

import main as main
def process(mod, arg):
    # def _call_func(func_name, args, kwargs, queue):
    #     func = getattr(main, func_name)
    #     result = func(*args, **kwargs)
    #     queue.put(result)

    func_name = mod
    args = arg
    kwargs = {}

    # queue = multiprocessing.Queue()
    # p = multiprocessing.Process(target=_call_func, args=(func_name, args, kwargs, queue))
    # p.start()
    # p.join()
    # result = queue.get()
    # return result
    try:
        func = getattr(main, func_name)
        return func(*args, **kwargs)
    except Exception as e:
        import traceback
        error_details = {
            "error_type": type(e).__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }
        print(error_details)
        return "!"+str(e)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=6002)
