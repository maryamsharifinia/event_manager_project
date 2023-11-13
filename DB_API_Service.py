# !/usr/bin/env python

# pylint: disable=invalid-name

from flask import Flask
from flask import request as req

app = Flask(__name__)

import importlib
import cherrypy
from marshmallow import Schema, fields

from helpers.communication_helpers import *
from helpers.config_helper import ConfigHelper
from helpers.io_helpers import RequiredFieldError

from walrus import *

from helpers.role_checker import RoleChecker


class InvalidConfigException(Exception):
    def __init__(self, param, value):
        super(InvalidConfigException, self).__init__("UNDEFINED PARAM %s: %s" % (param, value))


class InvalidInputException(Exception):
    def __init__(self, param, value):
        super(InvalidInputException, self).__init__("INVALID INPUT %s: %s" % (param, value))


class PermissionDeniedException(Exception):
    def __init__(self):
        super(PermissionDeniedException, self).__init__("PERMISSION DENIED")


class NotAuthenticatedException(InvalidInputException):
    def __init__(self):
        super(NotAuthenticatedException, self).__init__("API_KEY", "Not Authenticated")


class NotAuthorizedException(InvalidInputException):
    def __init__(self):
        super(NotAuthorizedException, self).__init__("token", "Not Authorized")


class NodeSchema(Schema):
    """
    Marshmallow schema for nodes object
    """
    name = fields.String(required=True)


def worker():
    """Background Timer that runs the hello() function every 5 seconds
    TODO: this needs to be fixed/optimized. I don't like creating the thread
    repeatedly.
    """

    # while True:
    #     t = threading.Timer(5.0, hello)
    #     t.start()
    #     t.join()


def authenticate(api_key):
    cfg_helper = ConfigHelper()
    if not cfg_helper.has_name("DB_API", api_key + "_service"):
        return None
    service_name = cfg_helper.get_config("DB_API")[api_key + "_service"]
    return service_name


# noinspection PyShadowingNames
def authorize(api_key, token, member_id):
    permitted_methods = None

    if api_key == token and member_id is None:  # CLIENT IS AN INTERNAL SERVICE
        return "SERVICE", "CLUB .*"

    member_type = None

    if member_id is None:
        raise RequiredFieldError("member_id")

    if token is None:
        raise RequiredFieldError("token")

    cfg_helper = ConfigHelper()

    redis_host = cfg_helper.get_config("DB_API")["redis_host"]
    redis_port = cfg_helper.get_config("DB_API")["redis_port"]
    redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

    cache_db = Database(redis_host, redis_port, redis_db_number)
    cache = cache_db.cache("authorization_cache")

    cache_record = cache.get(member_id)
    cache_token = None
    if cache_record is not None:
        cache_record = json.loads(cache_record)
        cache_token = cache_record["token"]
        member_type = cache_record["member_type"]
        permitted_methods = cache_record["permitted_methods"]

    if cache_token is None or token != cache_token:
        return None, None
    else:
        return member_type, permitted_methods


# noinspection PyShadowingNames
def execute_request(index, method_type, method, order_data, ip, api_key, token, member_id):
    role_checker = RoleChecker()
    cfg_helper = ConfigHelper()
    config_key = index.upper()

    if config_key not in cfg_helper.config.keys():
        raise InvalidInputException("TABLE", index)

    source = authenticate(api_key)
    if source is None:
        raise NotAuthenticatedException()

    member_type, permitted_methods = authorize(api_key=api_key, token=token, member_id=member_id)
    if member_type is None:
        raise NotAuthorizedException()

    if "," + source + "," not in cfg_helper.get_config(config_key)[method_type + "_permitted_sources"]:
        raise PermissionDeniedException()

    if source == "ADMIN":
        if not role_checker.check_role(member_permitted_methods=permitted_methods,
                                       service_name=config_key, method_name=method):
            raise PermissionDeniedException()

    tracking_code = str(uuid.uuid4())
    size = 1000 if "size" not in order_data else order_data["size"]
    from_ = 0 if "from" not in order_data else order_data["from"]
    sort_by = [{"DC_CREATE_TIME": "desc"}] if "sort_by" not in order_data or len(
        order_data["sort_by"].keys()) == 0 else [order_data["sort_by"]]

    request = {"broker_type": cfg_helper.get_config("DEFAULT")["broker_type"], "source": source,
               "method": method, "ip": ip, "api_key": api_key, "size": size, "from": from_,
               "tracking_code": tracking_code, "member_id": member_id, "member_type": member_type,
               "sort_by": sort_by, "data": order_data}

    dynamic_module = importlib.import_module(config_key.lower())

    class_ = config_key.split("_")
    class_name = ''
    for j in class_:
        class_name += (j[0].upper() + j[1:].lower())

    worker = getattr(dynamic_module, class_name + method_type[0].upper() + method_type[1:].lower() + "Worker")
    response = clear_response(worker().serve_request(request))

    return response, tracking_code


@app.route('/StudentScientificSociety/login', methods=['POST'])
def login():
    method_type = "login"
    try:
        order_data = req.get_json()

        api_key = order_data["api_key"]
        ip = req.remote_addr

        index = "members"
        method = order_data["method_type"]

        order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

        if "data" not in order_data.keys():
            raise RequiredFieldError("data")

        cfg_helper = ConfigHelper()
        config_key = index.upper()
        if config_key not in cfg_helper.config.keys():
            raise InvalidInputException("TABLE", index)

        source = authenticate(api_key)
        if source is None:
            raise NotAuthenticatedException()

        if "," + source + "," not in cfg_helper.get_config(config_key)[method_type + "_permitted_sources"]:
            raise PermissionDeniedException

        tracking_code = str(uuid.uuid4())
        size = 1000 if "size" not in order_data else order_data["size"]
        from_ = 0 if "from" not in order_data else order_data["from"]
        request = {"broker_type": cfg_helper.get_config("DEFAULT")["broker_type"], "source": source,
                   "method": method, "ip": ip, "api_key": api_key, "size": size, "from": from_,
                   "tracking_code": tracking_code,
                   "member_id": None, "data": order_data["data"]
                   }

        dynamic_module = importlib.import_module(config_key.lower())
        worker = getattr(dynamic_module, "MembersLoginWorker")
        response = clear_response(worker().serve_request(request_body=request))

        if method == "login" and response["is_successful"] is True:
            token = response["data"]["token"]
            member_id = response["data"]["member_id"]
            ttl = response["data"]["ttl"]
            member_type = response["data"]["member_type"]
            permitted_methods = response["data"]["member_permitted_methods"]

            redis_host = cfg_helper.get_config("DB_API")["redis_host"]
            redis_port = cfg_helper.get_config("DB_API")["redis_port"]
            redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

            free_member_id = cfg_helper.get_config("MEMBERS")["free_member_id"]
            free_token = cfg_helper.get_config("MEMBERS")["free_token"]
            free_ttl = cfg_helper.get_config("MEMBERS")["free_ttl"]

            cache_db = Database(redis_host, redis_port, redis_db_number)
            _cache = cache_db.cache("authorization_cache")
            cache_token = _cache.get(str(member_id))
            if cache_token is None:
                _cache.set(str(member_id), json.dumps({"token": token, "member_type": member_type,
                                                       "permitted_methods": permitted_methods}), ttl)
            else:
                cache_token = json.loads(cache_token)
                response["data"]["token"] = cache_token["token"]
                # response["data"]["token"] = free_token
                _cache.set(str(member_id), json.dumps(
                    {"token": response["data"]["token"], "member_type": cache_token["member_type"],
                     "permitted_methods": permitted_methods}), ttl)

            _cache.set(free_member_id, json.dumps({"token": free_token, "member_type": "FREE",
                                                   "permitted_methods": "CLUB"}), free_ttl)
        return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                "response": response}
    except NotAuthenticatedException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except NotAuthorizedException as e:
        return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except PermissionDeniedException as e:
        return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except RequiredFieldError as e:
        return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except InvalidInputException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except KeyError as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type,
                "error": "key %s is not passed" % str(e)}

    except:
        return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


@app.route('/StudentScientificSociety/logout', methods=['POST'])
def logout():
    method_type = "logout"
    try:
        order_data = req.get_json()

        api_key = order_data["api_key"]
        ip = req.remote_addr
        token = order_data["token"]
        member_id = order_data["member_id"]

        index = "clubmember"
        method = order_data["method_type"]

        order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

        if "data" not in order_data.keys():
            raise RequiredFieldError("data")

        cfg_helper = ConfigHelper()
        config_key = index.upper()
        if config_key not in cfg_helper.config.keys():
            raise InvalidInputException("TABLE", index)

        response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                  order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                  member_id=member_id)

        if method == "logout" and response["is_successful"] is True:
            member_id = member_id
            ttl = 1

            redis_host = cfg_helper.get_config("DB_API")["redis_host"]
            redis_port = cfg_helper.get_config("DB_API")["redis_port"]
            redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

            cache_db = Database(redis_host, redis_port, redis_db_number)
            _cache = cache_db.cache("authorization_cache")
            cache_token = _cache.get(member_id)
            if cache_token is None:
                pass
            else:
                _cache.set(member_id, json.dumps(
                    {"token": None, "member_type": None,
                     "permitted_methods": None}), ttl)

        return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                "response": response}
    except NotAuthenticatedException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except NotAuthorizedException as e:
        return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except PermissionDeniedException as e:
        return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except RequiredFieldError as e:
        return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except InvalidInputException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except KeyError as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type,
                "error": "key %s is not passed" % str(e)}

    except:
        return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


@app.route('/StudentScientificSociety/insert_request', methods=['POST'])
def index_insert():
    method_type = "insert"
    try:
        order_data = req.get_json()

        api_key = order_data["api_key"]
        ip = req.remote_addr
        token = order_data["token"]
        member_id = order_data["member_id"]

        index = order_data["table"]
        if "method_type" in order_data:
            method = order_data["method_type"]
            if method.upper() in ["UPDATE", "SELECT", "DELETE"]:
                raise PermissionDeniedException()
        else:
            method = "insert"

        if "data" not in order_data.keys():
            raise RequiredFieldError("data")

        order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

        response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                  order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                  member_id=member_id)

        return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                "response": response}
    except NotAuthenticatedException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except NotAuthorizedException as e:
        return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except PermissionDeniedException as e:
        return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except RequiredFieldError as e:
        return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except InvalidInputException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except KeyError as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type,
                "error": "key %s is not passed" % str(e)}
    except:
        import traceback
        traceback.print_exc()
        return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


@app.route('/StudentScientificSociety/delete_request', methods=['POST'])
def index_delete():
    method_type = "delete"
    try:
        # lock = db.lock('api_Lock', 1000)
        order_data = cherrypy.request.json

        api_key = order_data["api_key"]
        ip = cherrypy.request.remote.ip
        token = order_data["token"]
        member_id = order_data["member_id"]

        index = order_data["table"]
        if "method_type" in order_data:
            method = order_data["method_type"]
            if method.upper() in ["UPDATE", "SELECT", "INSERT"]:
                raise PermissionDeniedException()
        else:
            method = "delete"

        response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                  order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                  member_id=member_id)

        return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                "response": response}
    except NotAuthenticatedException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except NotAuthorizedException as e:
        return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except PermissionDeniedException as e:
        return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except InvalidInputException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except KeyError as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type,
                "error": "key %s is not passed" % str(e)}
    except:
        return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


@app.route('/StudentScientificSociety/update_request', methods=['POST'])
def index_update():
    method_type = "update"
    try:
        order_data = req.get_json()

        api_key = order_data["api_key"]
        ip = req.remote_addr
        token = order_data["token"]
        member_id = order_data["member_id"]

        index = order_data["table"]
        if "method_type" in order_data:
            method = order_data["method_type"]
            if method.upper() in ["INSERT", "SELECT", "DELETE"]:
                raise PermissionDeniedException()
        else:
            method = "update"

        response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                  order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                  member_id=member_id)

        return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                "response": response}
    except NotAuthenticatedException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except NotAuthorizedException as e:
        return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except PermissionDeniedException as e:
        return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except RequiredFieldError as e:
        return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except InvalidInputException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except KeyError as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type,
                "error": "key %s is not passed" % str(e)}
    except:
        return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}


@app.route('/StudentScientificSociety/select_request', methods=['POST'])
def index_select():
    method_type = "select"
    try:
        order_data = req.get_json()

        api_key = order_data["api_key"]
        ip = req.remote_addr
        token = order_data["token"]
        member_id = order_data["member_id"]

        index = order_data["table"]
        if "method_type" in order_data:
            method = order_data["method_type"]
            if method.upper() in ["UPDATE", "INSERT", "DELETE"]:
                raise PermissionDeniedException()
        else:
            method = "select"

        response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                  order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                  member_id=member_id)

        return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                "response": response}

    except NotAuthenticatedException as e:
        return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except NotAuthorizedException as e:
        return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except PermissionDeniedException as e:
        return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except RequiredFieldError as e:
        return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except InvalidInputException as e:
        return {"status": 400, "tracking_code": None, "method_type": method_type, "error": str(e)}
    except KeyError as e:
        return {"status": 400, "tracking_code": None, "method_type": method_type,
                "error": "key %s is not passed" % str(e)}
    except:
        return {"status": 500, "tracking_code": None, "method_type": None}


if __name__ == '__main__':
    app.run(debug=True,port=int(sys.argv[1]))
