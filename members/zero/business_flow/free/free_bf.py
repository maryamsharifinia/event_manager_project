from hashlib import md5
import members as service
from helpers.business_flow_helpers import BusinessFlow

from helpers.io_helpers import *
from members.zero.utils.utils import *


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

        if request["method"] == "register":
            check_required_key(['password_confirm', 'password', "user", "phone","email"], data)
            data["phone"] = (data["phone"]).replace(" ", "")
            data["email"] = data["email"]
            new_pass = data["password"]
            new_pass_confirm = data["password_confirm"]
            if new_pass != new_pass_confirm:
                raise PermissionError()
            md5_password = md5(new_pass.encode()).hexdigest().upper()
            data["pass_salt"], data["pass_hash"] = service.create_salt_and_hash(md5_password)

            data = check_full_schema(data, service.clubmembers_schema)
            data = preprocess(data, schema=service.clubmembers_schema)
            query = get_insert_check_query(data, service.clubmembers_schema)
            if len(list(self.index.find(query))) != 0:
                raise DuplicatedMember()

            self.index.insert_one({**data, "_id": data["phone"]})
            result = {"status": "inserted_person"}

        else:
            raise PermissionError()

        return result

    def delete_business_flow(self, data, request, member, params=None):
        raise PermissionError()

    def update_business_flow(self, data, request, member, params=None):
        raise PermissionError()
