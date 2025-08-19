# DEV

pm2 start gunicorn   --name Pymodule   --interpreter python3   --   pymodule:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6002 -w 10

pm2 start gunicorn   --name OCR   --interpreter python3   --   OCR:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6001 -w 3



# PROD

pm2 start main --name PROD-goModule

pm2 start gunicorn   --name PROD-Pymodule   --interpreter python3   --   pymodule:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6012 -w 10

pm2 start gunicorn   --name PROD-OCR   --interpreter python3   --   OCR:app -k uvicorn.workers.UvicornWorker -b 127.0.0.1:6011 -w 4


# CustomFloodfill
g++ -O3 -Wall -shared -std=c++14 -fPIC \
    $(python3.12-config --includes) \
    -I$(python3.12 -m pybind11 --includes | cut -c3-) \
    $(pkg-config --cflags opencv4) \
    -o customFloodFill$(python3.12-config --extension-suffix) app.cpp \
    $(python3.12-config --ldflags) \
    $(pkg-config --libs opencv4) -I include

#flipMatch
g++ -O3 -Wall -shared -std=c++14 -fPIC \
    $(python3.12-config --includes) \
    -I$(python3.12 -m pybind11 --includes | cut -c3-) \
    $(pkg-config --cflags opencv4) \
    -o flipMatch$(python3.12-config --extension-suffix) flip.cpp \
    $(python3.12-config --ldflags) \
    $(pkg-config --libs opencv4) -I include