from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper
from members.zero.utils.utils import *
import members as service

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
        raise PermissionError()

    def delete_business_flow(self, data, request, member, params=None):
        raise PermissionError()

    def update_business_flow(self, data, request, member, params=None):
        data = data['data']
        if request["method"] == "update_permission":
            data['permitted_methods'] = 'EVENTS\..*'
            check_schema(data, service.clubmembers_schema)
            data = preprocess(data, schema=service.clubmembers_schema)
            return update_member(self.index, data)
