
from helpers.business_flow_helpers import BusinessFlow
from events.zero.utils.utils import *
import events as service


class FreeBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(FreeBusinessFlowManager, self).__init__(service.service_name)

        self.cfg_helper = ConfigHelper()

        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])

    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]

        if method == "select":
            pass
        else:
            raise PermissionError()

        results = []
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
