import pymongo
from helpers.config_helper import ConfigHelper


class BusinessFlow:
    def __init__(self, service_name):
        self.cfg_helper = ConfigHelper()
        self.service_name = service_name.upper()
        self.mongo = pymongo.MongoClient("mongodb://localhost:27017/").myclient[self.service_name]

        if "index_name" in self.cfg_helper.get_config(self.service_name).keys():
            self.index_name = self.cfg_helper.get_config(self.service_name)["index_name"]

    def insert_business_flow(self, data, request, member, params=None):
        pass

    def update_business_flow(self, data, request, member, params=None):
        pass

    def delete_business_flow(self, data, request, member, params=None):
        pass

    def select_business_flow(self, data, request, member, params=None):
        pass

    def get_mongo_connection(self):
        self.mongo = pymongo.MongoClient("mongodb://localhost:27017/").myclient[self.service_name]

    def create_index(self, raw_index_name):
        return self.mongo.mydb[raw_index_name]

    def insert_file(self, raw_index_name, file, _type, _id):
        self.get_mongo_connection()
        mydb = self.mongo['files']
        mycol = mydb[raw_index_name]
        mydict = {"file_content": file, "type": _type, "_id": _id}
        return mycol.insert_one(mydict)

    def serve_file(self, raw_index_name, _id):
        self.get_mongo_connection()
        mydb = self.mongo['files']
        mycol = mydb[raw_index_name]
        myquery = {"_id": _id}
        return list(mycol.find(myquery))
