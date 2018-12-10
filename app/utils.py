import os
import Configs

async def GetDirFile(path):
    all_files = os.listdir(path)
    data = {"path": "./", "entities": []}
    for each_file in all_files:
        template = {"name": each_file,
                    "mtime": os.path.getmtime(os.path.join(path, each_file)),
                    "isdir": os.path.isdir(os.path.join(path, each_file)),
                    "size": os.path.getsize(os.path.join(path, each_file))
                    }
        data["entities"].append(template)
    return {"status": 200, "data": data, "error": ""}


def UpdateDictWithDict(target, source):
    for (k, v) in source.items():
        if target.get(k, "False") != "False":
            if isinstance(target[k],type({})):
                result = UpdateDictWithDict(target[k], source[k])
                target[k] = result["data"]
            else:
                target[k] = source[k]
        else:
            return {"status": 400, "data": '', "error": "Bad UpdateDoc"}
    return {"status": 200, "data": target, "error": ""}
