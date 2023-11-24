from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import events as service
from helpers.io_helpers import *


class UserBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(UserBusinessFlowManager, self).__init__(service.service_name)
        self.cfg_helper = ConfigHelper()

        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])

    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]

        method = request["method"]
        data = data["data"]
        if method == "select_event":
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))

            query = preprocess_schema(data, schema=service.event_schema)
            total = len(list(self.index.find(query)))

            search_result = list(self.index.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))
            for item in search_result:
                if item["image"] not in ['null', None, "None"]:
                    item["image"] = self.serve_file(service.service_name, item["image"])

            results = {"total": total, "result": list(search_result)}
        return {}

    def insert_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]
        if method == "insert":
            pass

        else:
            raise PermissionError()

        return []

    def delete_business_flow(self, data, request, member, params=None):
        raise PermissionError()

    def update_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        if request["method"] == "update":
            pass
        else:
            raise PermissionError()

        return []
