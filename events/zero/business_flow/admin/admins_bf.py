import datetime

from events.zero.utils.utils import *
from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import events as service

# noinspection PyMethodMayBeStatic
from helpers.io_helpers import *


class AdminBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(AdminBusinessFlowManager, self).__init__(service.service_name)

        self.cfg_helper = ConfigHelper()
        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])

    # noinspection PyUnusedLocal
    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]

        if method == "select":
            pass
        elif method == "selec_active":
            pass
        else:
            raise PermissionError()

        results = []

        return {"results": results}

    def insert_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
        data = data['data']
        method = request["method"]

        if method == "insert_event":
            check_required_key([], data)
            if 'image' in data:
                image_id = self.insert_file(service.service_name, data['image']['file_content'],
                                            data['image']['file_type'],
                                            member["_id"] + "@" + datetime.datetime.now().strftime(
                                                "%Y%m%d_%H:%M:%S.%f"))
            data = check_full_schema(data, service.event_schema)
            data = preprocess(data, schema=service.event_schema)
            data['image'] = image_id
            query = get_insert_check_query(data, service.event_schema)
            if list(self.index.find(query)) != 0:
                raise DuplicatedEvent()

            self.index.insert_one({**data, "_id": data["phone"]})
            results = {"status": "inserted_event"}
        elif method == "selec_active":
            pass
        else:
            raise PermissionError()

        return {"results": results}

    def delete_business_flow(self, data, request, member, params=None):
        raise PermissionError()

    def update_business_flow(self, data, request, member, params=None):
        raise PermissionError()
