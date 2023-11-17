from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import members as service


class UserBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(UserBusinessFlowManager, self).__init__(service.service_name)
        self.cfg_helper = ConfigHelper()

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

        if request["method"] == "update":
            pass
        else:
            raise PermissionError()

        return []
