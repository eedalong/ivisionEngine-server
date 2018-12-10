from aiohttp import web
import asyncio
import json

# TODO modify this to from . import xxx after test passed
'''
from . import MongoDB
from . import utils
from . import DataTransformer
from . import MarathonLayer
from . import Configs
from . import IO
'''
import MongoDB
import utils
import DataTransformer
import MarathonLayer
import Configs
import IO
from bson.objectid import ObjectId
import os
import requests
import logging
import aiohttp_mako
routes = web.RouteTableDef()
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@routes.get('/')
@aiohttp_mako.template('index.html')
async def handler(request):
    return {}

@routes.get('/api/_inspect')
async def Inspect(request):
    # TODO maintenance status should be checked from database
    body = {"version": "1.0.0",
            "maintenance": False,
            "features": [],
            "limits": {
                "task.assets_archive.max_size": 50,
                "archive.compression.supported_file_types": [".zip"],
                "archive.compression.supported_file_types": [".zip"]
            },
            "task_options": {
                "name": " type:string, note:experiment name",
                "description": "type:string note:experiment description",
                "tags": "type: List[string], note:experiment tags(for search)",
                "user_env": "type:List[string], note:user environment setting",
                "args": "type: List[string], note: args from users ",
                "container": {
                    "type": "Docker",
                    "image": "type: string note:container name "
                },
                "options": {
                    "work_dir": "type: string, note:work_dir for messos"
                },
                "resources": {
                    "memory": "type: int(M),note:memory use",
                    "cpu": "type:float, note:cpu use",
                    "gpu": "type:int, note:cpu use",
                    "disk": "type:int, note: disk use",
                    "port": "type:List[int], note:ports asked for"
                },
                "dependency": "List[string] note: code files and data files path need to run the program"
            },
            "work_dir": {
                "type": "string",
                "description": "Working directory of the task"
            }

            }
    return web.Response(status=200, body=json.dumps(body))


@routes.post('/api/v1/task/_query')
async def TaskBrows(request):
    query = json.loads(await request.json())
    DBoperation = MongoDB.MonoDBOperation()
    # Only support for key word query now
    result = await DBoperation.QueryDB(
        query["query"] if query.get("query", False) else {})
    for index in range(len(result["data"])):
        result["data"][index]["id"] = str(result["data"][index]["_id"])
        result["data"][index].pop("_id")
    return web.Response(status=result["status"],
                        body=json.dumps(result["data"][
                                        query["skip"]:query["skip"] + query[
                                            "limit"]]),
                        content_type="application/json", reason=result["error"])


@routes.get("/api/v1/update_status/{task_id}/{status}")
async def TaskStatusUpdate(request):
    task_id = request.match_info.get("task_id", "Wrong Task ID")
    task_status = request.match_info.get("status", "Wrong Task STATUS")
    try:
        ObjectId(task_id)
    except:
        logger.info("Invalid Task ID")
        return web.Response(status=400,
                            body={"error": 400, "reason": "Invalid Task ID",
                                  "description": ""},
                            content_type="application/json")
    # Update Task DOC ===> Finished
    # 2. query task doc info
    DBoperation = MongoDB.MonoDBOperation()
    query_result = await DBoperation.QueryDB({"_id": ObjectId(task_id)})
    if len(query_result["data"]) == 0:
        return web.Response(status=404,
                            body={"error": 404, "reason": "Invalid Task ID",
                                  "description": ""})

    # 3. update task doc info
    task_doc = query_result["data"][0]
    task_doc["status"] = task_status
    logger.debug("check updated task doc = {}".format(task_doc))
    update_result = await DBoperation.UpdateDBbyReplace(
        {"_id": ObjectId(task_id)},
        task_doc)
    logger.debug("check task status = {}".format(task_status))
    # if the task is finished, should kill the task
    if task_status == "COMPLETED":
        url = Configs.Marathon_ADDRESS + "/v2/apps/{app_id}/".format(
            app_id="mlge1." + task_id)
        response = requests.delete(url=url)
        logger.debug(
            "check delete response from marathon = {}".format(response.json()))
    return web.Response(status=200)


@routes.get("/api/v1/task/{task_id}")
async def GetTaskDoc(request):
    task_id = request.match_info.get("task_id", "Wrong Task ID")
    try:
        task_id = ObjectId(task_id)
    except:
        logger.info("Invalid Task ID")
        return web.Response(status=400,
                            body={"error": 400, "reason": "Invalid Task ID",
                                  "description": ""},
                            content_type="application/json")
    DBoperation = MongoDB.MonoDBOperation()
    result = await DBoperation.QueryDB({"_id": task_id})
    for index in range(len(result["data"])):
        result["data"][index]["id"] = str(result["data"][index]["_id"])
        result["data"][index].pop("_id")
    return web.Response(status=result["status"],
                        body=json.dumps(result["data"]),
                        content_type="application/json", reason=result["error"])


@routes.post("/api/v1/task/{task_id}/_update")
async def UpdateTaskDoc(request):
    task_id = request.match_info.get("task_id", "Wrong Task ID")
    update_doc = json.load(await request.json())
    try:
        task_id = ObjectId(task_id)
    except:
        return web.Response(status=400, reason="Invalid Task ID")
    query = json.loads(request.json())
    DBoperation = MongoDB.MonoDBOperation()
    result = await  DBoperation.UpdateDBbyReplace(task_id, update_doc)
    return web.Response(status=result["status"],
                        body=json.dumps(result["data"]), reason=result["error"])


@routes.get("/api/v1/task/{task_id}/_listdir/{path}")
async def ListFile(request):
    task_id = request.match_info.get("task_id", "Wrong Task ID")
    logger.debug("listfile task id check = {}".format(task_id))
    try:
        ObjectId(task_id)
    except:
        logger.debug("Task ID invalid = {}".format(str(task_id)))
        return web.Response(status=404,
                            body={"error": 404, "reason": "Invalid Task ID",
                                  "description": ""})
    path = request.match_info.get("path", "/")
    root = os.path.join(Configs.WORKDIR_PREFIX, str(task_id))
    if path != "WORKDIR":
        path = os.path.join(root,path)
    else:
        path = root
    logger.debug("check query path = {}".format(path))
    if not os.path.exists(path):
        logger.debug("path {} not exists".format(path))
        return web.Response(status=404, body={"error": 404,
                                              "reason": "path not exists",
                                              "description": ""})
        # TODO Something Wrong with the path
    result = await utils.GetDirFile(path)
    logger.debug("check list dir result = {}".format(result))
    return web.Response(status=200, body=json.dumps(result["data"]))


@routes.post("/api/v1/task/_create")
async def CreateTask(request):
    task_request = json.loads(await request.json())

    # 1 check the archive file size and judge the validation
    if task_request.get("archive", ""):
        archive_size = len(task_request["archive"]["data"])
        if archive_size > Configs.MAX_SIZE:
            return web.Response(status=413, body={"error": 413,
                                                  "reason": "Request Entity Too Large",
                                                  "description": ""},
                                content_type="application/json")
    # 2 add task to DB
    task_doc = DataTransformer.TaskRequest2TaskDoc(task_request)
    DBoperation = MongoDB.MonoDBOperation()
    result = await DBoperation.AddDB(task_doc)
    task_id = result["data"]
    task_doc["id"] = task_id
    task_doc.pop("_id")
    # 3 send response to client
    response = web.Response(status=200, body=json.dumps(task_doc),
                            content_type="application/json")
    await  response.prepare(request)
    await  response.write_eof()
    # 4 make work dir for this task
    await IO.MakeWorkDir(task_id, logger)
    # 5 extract file
    if task_request.get("archive", ""):
        await IO.FileExtract(task_id, task_request["archive"]["type"],
                             task_request["archive"]["data"], logger)
    return response


@routes.post("/api/v1/task/{task_id}/_start")
async def LaunchTask(request):
    # 1. check task id validation
    task_id = request.match_info.get("task_id", "Wrong Task ID")
    task_request = json.loads(await request.json())
    logger.debug("launchtask  task id check = {}".format(task_id))
    try:
        ObjectId(task_id)
    except:
        logger.debug("Task ID invalid = {}".format(str(task_id)))
        return web.Response(status=404,
                            body={"error": 404, "reason": "Invalid Task ID",
                                  "description": ""})
    # 2. query task doc info
    DBoperation = MongoDB.MonoDBOperation()
    query_result = await DBoperation.QueryDB({"_id": ObjectId(task_id)})
    if len(query_result["data"]) == 0:
        return web.Response(status=404,
                            body={"error": 404, "reason": "Invalid Task ID",
                                  "description": ""})

    # 3. update task doc info
    task_doc = query_result["data"][0]
    task_doc["status"] = "WAITING"
    logger.debug("check updated task doc = {}".format(task_doc))
    update_result = await DBoperation.UpdateDBbyReplace(
        {"_id": ObjectId(task_id)},
        task_doc)

    # 4. return response to client
    task_doc = update_result["data"]
    logger.debug("check update result = {}".format(task_doc))
    task_doc["id"] = str(task_doc["_id"])
    task_doc.pop("_id")
    response = web.Response(status=200, body=json.dumps(task_doc))
    await response.prepare(request)
    await response.write_eof()

    # submit task to marathon
    marathon_request = DataTransformer.TaskDoc2MarathonRequest(
        task_doc,
        task_id)
    # marathon_response, status = await MarathonLayer.MarathonPost(
    #    "http://192.168.64.57:8080/v2/apps", json_data=marathon_request)
    marathon_response = requests.post(Configs.Marathon_ADDRESS + "/v2/apps",
                                      json=marathon_request)
    status = marathon_response.status_code
    marathon_response = marathon_response.json()
    logger.debug("marathon task commit successfully")
    if status >= 400:
        logger.error(
            "marathon create task failed , status = {} and response = {}".format(
                status, marathon_response))
    # update task doc
    update_task_doc = DataTransformer.MarathonResponse2TaskDoc(
        marathon_response)
    result = await DBoperation.UpdateDBbyReplace({"_id": ObjectId(task_id)},
                                                 update_task_doc)
    if result["status"] != 200:
        logger.error(
            "update task doc error, update doc = {}".format(update_task_doc))
    logger.debug("task doc DB update successfully")
    return response


@routes.post("/api/v1/task/{task_id}/_kill")
async def KillTask(request):
    task_id = request.match_info.get("task_id", "Wrong Task ID")
    logger.debug("KillTask: task id check = {}".format(task_id))
    try:
        ObjectId(task_id)
    except:
        logger.debug("Task ID invalid = {}".format(str(task_id)))
        return web.Response(status=404,
                            body={"error": 404, "reason": "Invalid Task ID",
                                  "description": ""})
    DBoperation = MongoDB.MonoDBOperation()
    query_result = await DBoperation.QueryDB({"_id": ObjectId(task_id)})
    if not len(query_result["data"]):
        return web.Response(status=404, body={"error": 404, "description": "",
                                              "reason": "the task doesn't exist"
                                              }
                            )
    task_doc = query_result["data"][0]
    # check task status
    if task_doc["status"] == "DEPLOYING" or task_doc["status"] == "RUNNING":
        # modify task status to KILLING
        task_doc["status"] = "KILLING"
        logger.debug("check updated task doc = {}".format(task_doc))
        update_result = await DBoperation.UpdateDBbyReplace(
            {"_id": ObjectId(task_id)},
            task_doc)
        # return response to client
        task_doc = update_result["data"]
        logger.debug("check update result = {}".format(task_doc))
        task_doc["id"] = str(task_doc["_id"])
        task_doc.pop("_id")
        response = web.Response(status=200, body=json.dumps(task_doc))
        await response.prepare(request)
        await response.write_eof()
        # submit kill request to marathon
        marathon_request = DataTransformer.TaskDoc2MarathonRequest(task_doc, task_id)
        marathon_response = requests.delete(Configs.Marathon_ADDRESS + "/v2/apps/{app_id}".format(app_id="mlge1." + task_id),
				)
        status = marathon_response.status_code
        marathon_response = marathon_response.json()
        logger.debug("kill request commit successfully")
        if status >= 400:
            # marathon cannot kill task
            logger.error(
                "marathon kill task failed , status = {} and response = {}".format(
                    status, marathon_response))
            return web.Response(status=409, body=json.dumps({"error": 409,
                                                             "reason": "marathon failure, task status: {}"
                                                            .format(status),
                                                             "description": ""
                                                             })
                                )
        # update task doc

        query_result = await DBoperation.QueryDB({"_id": ObjectId(task_id)})

        task_doc = query_result["data"][0]
        task_doc["status"] = "KILLED"
    # check task status
        logger.debug("check updated task doc = {}".format(task_doc))
        result = await DBoperation.UpdateDBbyReplace({"_id": ObjectId(task_id)}, task_doc)
        if result["status"] != 200:
            logger.error(
                "update task doc error, update doc = {}".format(task_doc))
        logger.debug("task doc DB update successfully")
        return response
    else:
        return web.Response(status=409, body=json.dumps({"error": 409,
                                                         "reason": "status failure, task status: {}"
                                                        .format(task_doc["status"]),
                                                         "description": ""
                                                         },

                                                        )
                            )


@routes.post("/api/v1/task/{task_id}/_delete")
async def DeleteTask(request):
    task_id = request.match_info.get("task_id", "Wrong Task ID")
    logger.debug("launchtask  task id check = {}".format(task_id))
    try:
        ObjectId(task_id)
    except:
        logger.debug("Task ID invalid = {}".format(str(task_id)))
        return web.Response(status=404,
                            body={"error": 404, "reason": "Invalid Task ID",
                                  "description": ""})
    DBoperation = MongoDB.MonoDBOperation()
    query_result = await DBoperation.QueryDB({"_id": ObjectId(task_id)})
    if not len(query_result["data"]):
        return web.Response(status=404, body={"error": 404, "description": "",
                                              "reason": "the task doesnot exist"
                                              }
                            )
    task_doc = query_result["data"][0]
    if task_doc["status"] == "WAITING" or task_doc["status"] == "CREATING" or \
            task_doc["status"] == "COMPLETED" or task_doc["status"] == "KILLED":
        await DBoperation.DelDB({"_id": ObjectId(task_id)})
        response = web.Response(status=200, body=json.dumps({}))
        await response.prepare(request)
        await response.write_eof()
        await IO.RMWorkDir(task_id, logger)
        return response
    else:
        return web.Response(status=409, body=json.dumps({"error": 409,
                                                         "reason": "the task status is {}"
                                                        .format(
                                                             task_doc[
                                                                 "status"]),
                                                         "description": ""
                                                         },

                                                        )
                            )


def init():
    app = web.Application()
    lookup = aiohttp_mako.setup(app, input_encoding='utf-8',
                                output_encoding='utf-8',
                                default_filters=['decode.utf8'])

    template = open(Configs.INDEX_PATH).read()

    lookup.put_string("index.html",template)
    app.router.add_routes(routes)
    return app


web.run_app(init(), host=Configs.Server_ADDRESS, port=Configs.Server_PORT)
loop = asyncio.get_event_loop()
print(loop)
