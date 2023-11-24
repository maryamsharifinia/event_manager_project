from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import members as service
from helpers.io_helpers import *
from members.zero.utils.utils import *


class UserBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(UserBusinessFlowManager, self).__init__(service.service_name)
        self.cfg_helper = ConfigHelper()
        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])

    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]

        if method == "select":
            pass

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
        result = {}
        data = data['data']
        if request["method"] == "update":
            check_schema(data, service.clubmembers_schema)
            data = preprocess(data, schema=service.clubmembers_schema)

            result = update_member(data, member)
        elif request["method"] == "change_password":
            check_required_key(["member_id", "old_password", "new_password"], data)
            result = change_password(data, member, self.index)
        else:
            raise PermissionError()

        return result
