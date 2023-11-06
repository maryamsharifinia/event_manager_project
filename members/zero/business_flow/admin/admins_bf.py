
from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import members as service


# noinspection PyMethodMayBeStatic
class AdminBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(AdminBusinessFlowManager, self).__init__(service.service_name)

        self.cfg_helper = ConfigHelper()

    # noinspection PyUnusedLocal
    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]

        if method == "select":
            pass
        elif method=="selec_active":
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
        raise PermissionError()
