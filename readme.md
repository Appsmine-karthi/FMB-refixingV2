# DEV

pm2 start gunicorn   --name Pymodule   --interpreter python3   --   pymodule:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6002 -w 10

pm2 start gunicorn   --name OCR   --interpreter python3   --   OCR:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6001 -w 3



# PROD

pm2 start main --name PROD-goModule

pm2 start gunicorn   --name PROD-Pymodule   --interpreter python3   --   pymodule:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6012 -w 10

pm2 start gunicorn   --name PROD-OCR   --interpreter python3   --   OCR:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6011 -w 4