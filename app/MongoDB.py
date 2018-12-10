import pymongo
import asyncio
from bson.objectid import ObjectId
import six
import utils

class MonoDBOperation:

    def __init__(self, DBName="TaskDB", CollectionName="TaskDoc"):
        self.DBName = DBName
        self.CollectionName = CollectionName
        connect = pymongo.MongoClient()
        self.DB = connect[DBName]
        self.Collect = self.DB[CollectionName]

    async def AddDB(self, addData):
        # add a data to DB and return the result

        result = self.Collect.insert(addData)
        return {"status": 200, "data": str(result), "error": ""}

    async def DelDB(self, dataId):

        try:
            self.Collect.remove(dataId)
        except:
            # TODO
            return {"status": 404, "data": "",
                    'error': "{} not found in dataset".format(dataId)}
        return {"status": 200, "data": "", 'error': ""}

    async def QueryDB(self, queryData):
        try:
            resultItor = self.Collect.find(queryData)
        except:
            return {"status": 400, "data": "", "error": "Bad QueryData"}
        queryResult = []
        for item in resultItor:
            queryResult.append(item)
        return {"status": 200, "data": queryResult, "error": ""}

    async def UpdateDBbyReplace(self, queryData, replaceData):
        # update the task doc by replace some items and return the updated task doc

        result = self.Collect.find_one(queryData)
        if not result:
            return {"status": 400, "data": '', "error": "Query Not Found"}
        result = utils.UpdateDictWithDict(result,replaceData)
        if result["status"] == 400:
            return result
        self.Collect.find_one_and_replace(queryData, result["data"])
        return result

