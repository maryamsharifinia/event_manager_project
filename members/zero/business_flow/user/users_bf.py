from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper
from walrus import *
import members as service
from helpers.io_helpers import *
from members.zero.utils.utils import *
import random


class UserBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(UserBusinessFlowManager, self).__init__(service.service_name)
        self.cfg_helper = ConfigHelper()
        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])

        redis_host = self.cfg_helper.get_config("REDIS")["redis_host"]
        redis_port = self.cfg_helper.get_config("REDIS")["redis_port"]
        redis_db_number = self.cfg_helper.get_config("REDIS")["redis_db_number"]

        self.db = Database(redis_host, redis_port, redis_db_number)

    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]

        if method == "select":
            pass

        return {}

    def insert_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
        data = data['data']
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

        elif request["method"] == "verify_email":
            otp_catch = self.db.cache("otp")
            otp = random.randint(1000, 9999)
            _id = str(uuid.uuid4())
            otp_catch.set(key=data["email"], timeout=20 * 60,
                          value=json.dumps({"correct": otp}))
            data["content"] = f'کد اعتبارسنجی شما :{otp}'
            send_email(data, "اعتبارسنجی ایمیل")
        elif request["method"] == "check_otp_email":
            if "otp" not in data.keys():
                raise RequiredFieldError("otp")
            elif "email" not in data.keys():
                raise RequiredFieldError("email")

            result = check_otp("email", data, self.db)
            if result["check"]:
                doc = {"_id": member["_id"],
                       "verify_email": "TRUE",
                       "email": data["email"]
                       }
                result = update_member(mongo=self.index, data=doc)
            else:
                raise InvalidOtp()

        else:
            raise PermissionError()

        return result
