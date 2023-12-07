from helpers.config_helper import ConfigHelper
from helpers.io_helpers import *
from flask import url_for, redirect

from suds.client import Client

MMERCHANT_ID = 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX'
ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'


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


def get_event_by_id(mongo, event_id):
    query = {
        "_id": event_id
    }

    search_result = list(mongo.mydb["events_info"].find(query))

    if len(search_result) != 1:
        raise EventNotFoundError()

    return search_result[0]


def register_event(event_info, mongo_register_event, member, registration_event_schema):
    query = {
        "member_id": member["_id"],
        "event_id": event_info["_id"],
    }

    search_result = list(mongo_register_event.find(query))

    if len(search_result) != 0:
        raise DuplicatedRegister()
    data = check_full_schema({**event_info, **member}, registration_event_schema)
    data['event_id'] = event_info['_id']
    data['event_name'] = event_info['name']
    data['member_id'] = member['_id']
    data['status'] = "SUBMITTED"
    data = preprocess(data, registration_event_schema)
    res = mongo_register_event.insert_one({**data, "_id": data['member_id'] + "_" + data['event_id']})

    result = {"id": res.inserted_id, "result": "inserted"}

    return result


def send_request(amount,
                 description,
                 email,
                 mobile, ):
    client = Client(ZARINPAL_WEBSERVICE)
    result = client.service.PaymentRequest(MMERCHANT_ID,
                                           amount,
                                           description,
                                           email,
                                           mobile,
                                           'https://www.w3schools.com/git/git_ignore.asp?remote=github')
    result.Status = 100
    result.Authority = "100"
    if result.Status == 100:
        return redirect('https://www.zarinpal.com/pg/StartPay/' + result.Authority)
    else:
        return 'Error'


def verify(amount, request):
    client = Client(ZARINPAL_WEBSERVICE)
    if request.get('Status') == 'OK':
        result = client.service.PaymentVerification(MMERCHANT_ID,
                                                    request['Authority'],
                                                    amount)
        if result.Status == 100:
            return 'Transaction success. RefID: ' + str(result.RefID)
        elif result.Status == 101:
            return 'Transaction submitted : ' + str(result.Status)
        else:
            return 'Transaction failed. Status: ' + str(result.Status)
    else:
        return 'Transaction failed or canceled by user'


def update_event(mongo, data):
    _id = data["_id"]
    del data["_id"]

    blocked_fields = []

    data_keys = list(data.keys())
    for k in data_keys:
        if k in blocked_fields:
            del data[k]

    myquery = {"_id": _id}
    newvalues = {"$set": {**data}}

    update_result = mongo.update_one(myquery, newvalues)

    result = {"id": _id, "result": update_result.raw_result}

    return result


class DuplicatedEvent(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(DuplicatedEvent, self).__init__(message="Member is already exist ",
                                              error_code=error_code_base + 101,
                                              persian_massage="رویدادی با این مشخصات وجود دارد.")


class EventNotFoundError(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(EventNotFoundError, self).__init__(message="event not exist",
                                                 error_code=error_code_base + 102,
                                                 persian_massage="رویدادی با این مشخصات وجود ندارد.")


class CapacityError(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(CapacityError, self).__init__(message="The capacity of this ticket is over",
                                            error_code=error_code_base + 103,
                                            persian_massage="ظرفیت این بلیط تموم شده است.")


class DuplicatedRegister(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(DuplicatedRegister, self).__init__(message="Member is already exist ",
                                                 error_code=error_code_base + 104,
                                                 persian_massage="قبلا در این رویداد ثبت نام شده است .")


class PaymentFailed(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(PaymentFailed, self).__init__(message="Payment Failed ",
                                            error_code=error_code_base + 105,
                                            persian_massage="پرداخت ناموفق بود .")
