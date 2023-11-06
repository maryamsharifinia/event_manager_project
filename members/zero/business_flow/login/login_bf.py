from helpers.io_helpers import *
from helpers.config_helper import ConfigHelper
from helpers.business_flow_helpers import BusinessFlow
from hashlib import md5
from uuid import uuid4
import members as service


class LoginBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(LoginBusinessFlowManager, self).__init__(service.service_name)
        self.cfg_helper = ConfigHelper()

        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])

    def login_business_flow(self, data, request):
        self.get_mongo_connection()

        if 'method' not in request.keys():
            raise RequiredFieldError("method")

        method = request["method"]
        if method == "login":
            if "user" not in data.keys():
                raise RequiredFieldError("user")
            if "pass" not in data.keys():
                raise RequiredFieldError("pass")

            data = preprocess(data, service.clubmembers_schema)
            resp = self.method_login(data=data)

        else:
            raise PermissionError()

        return resp

    def method_login(self, data):
        username = data["user"]
        can_login_with_username, member = self.login_with_username(data=data, username=username)

        if not can_login_with_username:
            raise service.IncorrectLoginData('Incorrect username or password')

        resp = {"token": str(uuid4()),
                "member_id": member["_id"],
                "ttl": 3600 * 5,
                "member_type": member["_source"]["category"],
                "member_first_name": member["_source"]["first_name"],
                "member_last_name": member["_source"]["last_name"],
                "member_username": member["_source"]["user"],
                "member_phone": member["_source"]["phone"],
                "member_national_id": member["_source"]["national_id"],
                "member_permitted_methods": member["_source"]["permitted_methods"],
                }

        return resp

    def login_with_username(self, data, username):
        login_result = False

        member = service.get_member_by_username(mongo=self.mongo, username=username, index_name=self.index_name, )

        if member["_source"] is not None and member["_source"]["pass_hash"] != 'null':
            raw_password = data["pass"]
            md5_password = md5(raw_password.encode()).hexdigest().upper()

            login_result = service.check_password(raw_password, member)

            if login_result is False:
                login_result = service.check_password(md5_password, member)

        return login_result, member
