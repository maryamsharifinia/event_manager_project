import base64
from hashlib import sha256
from uuid import uuid4
from helpers.config_helper import ConfigHelper
from helpers.io_helpers import MemberNotFoundError, UserInputError, RequiredFieldError


def get_member(mongo, request_sender_id):
    query = {"_id": request_sender_id}

    search_result = list(mongo.mydb["member_info"].find(query))

    if len(search_result) != 1:
        raise MemberNotFoundError()

    return search_result[0]


def get_member_by_username(mongo, username, index_name):
    query = {"user": username}
    search_result = list(mongo.mydb[index_name].find(query))

    request_sender_member = {"_source": None, "_id": None}

    if len(search_result) == 1:
        request_sender_member = {"_source": search_result[0],
                                 "_id": search_result[0]["_id"]}

    return request_sender_member


def check_password(password, member):
    real_hash = member["_source"]["pass_hash"]

    bytes_obj = (password + member["_source"]["pass_salt"]).encode("utf-16-le")

    sha_digest = sha256(bytes_obj).digest()
    pass_hash = base64.b64encode(sha_digest)

    if pass_hash.decode() == real_hash:
        return True
    else:
        return False


def create_salt_and_hash(md5_password):
    salt = str(uuid4())

    bytes_obj = (md5_password + salt).encode("utf-16-le")

    sha_digest = sha256(bytes_obj).digest()
    _hash = base64.b64encode(sha_digest).decode()

    return salt, _hash


def get_insert_check_query(data, schema):
    query = {}
    for key in data.keys():
        if key not in schema.keys():
            continue
        if "_check_in_insert" in schema[key].keys() and schema[key]["_check_in_insert"] is False:
            continue
        else:
            query.update({key: data[key]})
    return query


def check_required_key(required_keys, data):
    for required_key in required_keys:
        if required_key not in data.keys():
            raise RequiredFieldError(required_key)


def update_member(mongo, data):
    _id = data["_id"]
    del data["_id"]

    blocked_fields = ["national_id", "is_active"]

    data_keys = list(data.keys())
    for k in data_keys:
        if k in blocked_fields:
            del data[k]

    if "permitted_methods" in data.keys() and data["permitted_methods"] != "CLUB":
        data["category"] = "ADMIN"
    elif "permitted_methods" in data.keys() and data["permitted_methods"] == "CLUB":
        data["category"] = "MEMBER"

    myquery = {"_id": _id}
    newvalues = {"$set": {**data}}

    update_result = mongo.update_one(myquery, newvalues)

    result = {"id": _id, "result": update_result.raw_result}

    return result


class IncorrectLoginData(UserInputError):
    def __init__(self, msg):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(IncorrectLoginData, self).__init__(message=msg, error_code=error_code_base + 101,
                                                 persian_massage='نام کاربری یا رمز عبور اشتباه است.')


class DuplicatedMember(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(DuplicatedMember, self).__init__(message="Member is already exist ",
                                               error_code=error_code_base + 102,
                                               persian_massage="کاربری با این مشخصات وجود دارد.")
