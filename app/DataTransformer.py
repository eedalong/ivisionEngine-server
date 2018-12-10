import time
from datetime import datetime
import six
import Configs


def parse_args(args):
    result_args = ""
    for arg in args:
        result_args = result_args + arg + " "
    return result_args


def TaskRequest2TaskDoc(task_request):
    task_doc = {"name": task_request.get("name", ""),
                "description": task_request.get("description", ""),
                "tags": task_request.get("tags", ""),
                "create_time": datetime.utcfromtimestamp(time.time()).strftime(
                    "%Y-%M-%D %H:%M:%S"),
                "start_time": "",
                "stop_time": "",
                "status": "CREATING",
                "error": {
                    "message": "",
                    "traceback": ""
                },
                "exit_code": "",
                "user_env": task_request.get("user_env", ""),
                "args": task_request.get("args", ""),
                "container": task_request.get("container",
                                              {"type": "", "image": ""}),
                "resources": {
                    "request": {
                        "memory": task_request["resources"]["memory"],
                        "cpu": task_request["resources"]["cpu"],
                        "gpu": task_request["resources"].get("gpu", ""),
                        "disk": task_request["resources"].get("disk", ""),
                        "port": task_request["resources"].get("port", []),
                    },
                    "assigned": {
                        "memory": "",
                        "cpu": "",
                        "gpu": "",
                        "disk": "",
                        "port": "",

                    }
                },
                "exc_info": {
                    "hostname": "",
                    "pid": "",
                    "work_dir": "",
                    "env": "",
                },
                "file_size": ""

                }
    return task_doc


def TaskRequest2MarathonRequest(task_request, task_id):
    marathon_request = {"id": task_id,
                        "cmd": "echo$(GREET_MESSAGE)",
                        "cpus": float(task_request["resources"]["cpu"]),
                        "mem": int(task_request["resources"]["memory"])
                        }
    if task_request["resources"].get("disk", False):
        marathon_request["disk"] = int(task_request["resources"]["disk"])
    '''
    if task_request["container"].get("image", False):
        marathon_request["container"]["image"] = task_request["container"][
            "image"]
    '''
    return marathon_request


def TaskDoc2MarathonRequest(task_doc, task_id):

    post_back_finished = "wget {address}:{port}/api/v1/update_status/{task_id}/COMPLETED".format(
        address=Configs.Server_ADDRESS, task_id=task_id,
        port=Configs.Server_PORT)
    post_back_start = "wget {address}:{port}/api/v1/update_status/{task_id}/RUNNING".format(
        address=Configs.Server_ADDRESS, task_id=task_id,
        port=Configs.Server_PORT)
    marathon_request = {"id": "mlge1.{}".format(task_id),
                        # TODO cmd should be parsed from user requests
                        "cmd": "{post_back_start} && cd {WORKDIR_PREFIX}/{task_id}/ &&"
                               "/bin/sh -c \" {user_command} > "
                               "{WORKDIR_PREFIX}/{task_id}/log/stdout "
                               "2>&1 \" && {post_back_finished} && rm COMPLETED && rm  RUNNING".format(
                            task_id=task_id,
                            WORKDIR_PREFIX=
                            Configs.WORKDIR_PREFIX,
                            user_command=parse_args(
                                task_doc[
                                    "args"]),
                            post_back_finished=post_back_finished,
                            post_back_start=post_back_start),
                        "acceptedResourceRoles": ["slave_public", "*"],
                        "cpus": task_doc["resources"]["request"]["cpu"],
                        "mem": task_doc["resources"]["request"][
                            "memory"],
                        "disk": 0,
                        "instance": 1,
                        "container": {
                            "type": "MESOS",
                            "docker": {
                                "forcePullImage": True,
                                "image":
                                    "docker.peidan.me/haowenxu/ml-runtime:gpu" if Configs.GPU else "docker.peidan.me/haowenxu/ml-runtime:cpu",
                                "parameters": [],
                                "privileged": False
                            },
                            "volumes": [
                                {
                                    "containerPath": "/mnt/mfs",
                                    "hostPath": "/mnt/mfs",
                                    "mode": "RW"
                                },
                                {
                                    "containerPath": "/home",
                                    "hostPath": "/home",
                                    "mode": "RW"

                                }

                            ],
                            "networks": [
                                {
                                    "mode": "host"
                                }
                            ],
                            "portDefinitions": [
                                {
                                    "port": 10086,
                                    "protoval": "tcp"
                                }
                            ],
                            "env": {
                                "GREETING_MESSAGE": "hello, world!"
                            }
                        },

                        }
    return marathon_request


def MarathonResponse2TaskDoc(marathon_response):
    task_doc = {
        "resources": {
            "assigned": {
                "memory": marathon_response["mem"],
                "cpu": marathon_response["cpus"],
                "gpu": marathon_response["gpus"],
                "disk": marathon_response["disk"],
                "port": marathon_response["portDefinitions"][0]["port"]
            }
        },
        "status": "DEPLOYING"
    }
    return task_doc
