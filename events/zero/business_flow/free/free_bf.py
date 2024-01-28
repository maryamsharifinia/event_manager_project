from helpers.business_flow_helpers import BusinessFlow
from events.zero.utils.utils import *
import events as service
from helpers.io_helpers import *


class FreeBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(FreeBusinessFlowManager, self).__init__(service.service_name)

        self.cfg_helper = ConfigHelper()

        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])

    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

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

            search_result = list(self.index.find(query).skip(from_value).limit(to_value - from_value).sort(sort, sort_type))

            results = {"total": total, "result": list(search_result)}
        else:
            raise PermissionError()

        return results

    def insert_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
        data = data['data']

        if request["method"] == "":
            raise PermissionError()

        else:
            raise PermissionError()

        return result

    def delete_business_flow(self, data, request, member, params=None):
        raise PermissionError()

    def update_business_flow(self, data, request, member, params=None):
        raise PermissionError()
