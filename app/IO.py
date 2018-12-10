import asyncio
import os
import shutil
import six
import logging
import mimetypes
import gzip
import tarfile
import rarfile
import zipfile
import base64
import time
import Configs
async def MakeWorkDir(task_id:str,logger:logging.Logger):
    # TODO TASK WORKDIR SHOULD BE CONFIRMED FROM FILE
    try:
        workdir = os.path.join(Configs.WORKDIR_PREFIX,task_id)
        os.makedirs(workdir,mode =0o777, exist_ok=True)
        os.makedirs("{workdir}/log/".format(workdir=workdir),mode =0o777, exist_ok=True)
        tmp_file = open("{workdir}/log/stdout".format(workdir=workdir),"w")
        tmp_file.close()
    except OSError as error:
        logger.error(error)
        return False
    return True
async def RMWorkDir(task_id:str,logger:logging.Logger):
    try:
        shutil.rmtree(os.path.join(Configs.WORKDIR_PREFIX,task_id))
    except:
        logger.error("rm workdir {} failed".format(os.path.join(Configs.WORKDIR_PREFIX,task_id)))
    return

async def FileWrite(task_id,file_content):
    name = str(time.time())
    file = open(os.path.join(os.path.join(Configs.WORKDIR_PREFIX,task_id),name),"wb")
    file.write(file_content)
    file.close()
    return os.path.join(os.path.join(Configs.WORKDIR_PREFIX,task_id),name)
async def Extract(task_id, fileobj):
    fileobj.extractall(path = os.path.join(os.path.join(Configs.WORKDIR_PREFIX,task_id)))
async def RemoveFile(file_path):
    os.remove(file_path)
async def FileExtract(task_id:str,file_type,file_content,logger:logging.Logger):
    #TODO support more file types
    file_obj = ""
    file_content = bytes(file_content,"ascii")
    file_content = base64.b64decode(file_content)
    file_name = await FileWrite(task_id, file_content)
    logger.debug("check file type  = {}".format(file_type))
    # zip compress support
    if file_type == "application/zip":
        file_obj = zipfile.ZipFile(open(file_name,"rb"))
    # tar file support
    if file_type == "application/x-tar":
        file_obj = tarfile.TarFile(file_name)
    await  Extract(task_id,file_obj)
    logger.info("extract file successfully")
    await  RemoveFile(file_name)
    return True
