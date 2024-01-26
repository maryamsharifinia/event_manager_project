import uuid
from hashlib import md5
import members as service
from helpers.business_flow_helpers import BusinessFlow
import random
from helpers.io_helpers import *
from members.zero.utils.utils import *
from walrus import *

class FreeBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(FreeBusinessFlowManager, self).__init__(service.service_name)

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
        else:
            raise PermissionError()

        results = []
        return results

    def insert_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
        data = data['data']

        if request["method"] == "register":
            check_required_key(['password_confirm', 'password', "user", "phone", "email"], data)
            data["phone"] = (data["phone"]).replace(" ", "")
            data["email"] = data["email"]
            new_pass = data["password"]
            new_pass_confirm = data["password_confirm"]
            if new_pass != new_pass_confirm:
                raise PermissionError()

            if len(re.findall('^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])[A-Za-z0-9@#$%^&+=\!\*]{8,}$', new_pass)) == 0:
                raise InvalidPasswordStructure()

            md5_password = md5(new_pass.encode()).hexdigest().upper()
            data["pass_salt"], data["pass_hash"] = service.create_salt_and_hash(md5_password)

            data = check_full_schema(data, service.clubmembers_schema)
            data = preprocess(data, schema=service.clubmembers_schema)

            if len(list(self.index.find({"user": data["user"]}))) != 0:
                raise DuplicatedMember()

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

        self.get_mongo_connection()
        result = {}
        data = data['data']

        if request["method"] == "update":
            check_schema(data, service.clubmembers_schema)
            data = preprocess(data, schema=service.clubmembers_schema)
            result = update_member(data, member)

        if request["method"] == "change_password":
            check_required_key(["member_id", "old_password", "new_password"], data)
            result = change_password(data, member, self.index)


        elif request["method"] == "check_verification_code_email":
            if "verification_code" not in data.keys():
                raise RequiredFieldError("verification_code")
            elif "email" not in data.keys():
                raise RequiredFieldError("email")
            result = check_verification_code("email", data, self.db)
            if result["check"]:
                doc = {"_id": member["_id"],
                       "verify_email": "TRUE",
                       "email": data["email"]
                       }
                result = update_member(mongo=self.index, data=doc)
            else:
                raise InvalidVerificationCode()


        elif request["method"] == "verify_email":
            verification_code_catch = self.db.cache("otp_forget_password")
            verification_code = random.randint(1000, 9999)
            _id = str(uuid.uuid4())
            verification_code_catch.set(key=data["email"], timeout=20 * 60,
                                        value=json.dumps({"correct": verification_code}))
            data["content"] = f'کد اعتبارسنجی شما :{verification_code}'
            return send_email(data, "اعتبارسنجی ایمیل")


        else:
            raise PermissionError()
