# Reunite-AI-Tracking-System-
D:\Projects\Reunite\venv310\Scripts\activate.bat
celery -A Reunite worker -l info -P solo

root@DESKTOP-HBTFQMB:/mnt/d/Projects/Reunite# redis-cli --version
    redis-cli 7.0.15
root@DESKTOP-HBTFQMB:/mnt/d/Projects/Reunite# redis-server --version
    Redis server v=7.0.15 sha=00000000:0 malloc=jemalloc-5.3.0 bits=64 build=62c7a5d52c72f4cd

root@DESKTOP-HBTFQMB:/mnt/d/Projects/Reunite# sudo service redis-server start