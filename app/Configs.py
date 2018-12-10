import logging
WORKDIR_PREFIX = "/home/yuanxiulong/TASK_WORKDIR"
MAX_SIZE = 50 * 1024 * 1024
GPU = 1
Marathon_ADDRESS = "http://mesos-cpu.cluster.peidan.me:8080"
Marathon_ADDRESS_GPU = "http://mesos-gpu.cluster.peidan.me:8080"
Server_ADDRESS = "0.0.0.0"
INDEX_PATH = "/home/yuanxiulong/SWE/dist/index.html"
Server_PORT = 7001

if GPU :
    Marathon_ADDRESS = Marathon_ADDRESS_GPU
    Server_PORT = 7002
