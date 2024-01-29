from helpers.config_helper import ConfigHelper
from helpers.io_helpers import *
import requests

MMERCHANT_ID = '1344b5d4-0048-11e8-94db-005056a205be'
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


def register_event(event_info, mongo_register_event, member, registration_event_schema, ticket_type):
    query = {
        "member_id": member["_id"],
        "event_id": event_info["_id"],
    }

    search_result = list(mongo_register_event.find(query))

    if len(search_result) != 0:
        current_ticket_type = search_result[0]['ticket_type']
        for i in list(ticket_type.keys()):
            current_ticket_type[i] += ticket_type[i]
        myquery = {"_id": search_result[0]["_id"]}
        newvalues = {"$set": {"ticket_type": current_ticket_type}}
        mongo_register_event.update_one(myquery, newvalues)
        result = {"id": search_result[0]["_id"], "result": "updated"}
        return result

    data = check_full_schema({**event_info, **member}, registration_event_schema)
    data['event_id'] = event_info['_id']
    data['event_name'] = event_info['name']
    data['member_id'] = member['_id']
    data['status'] = "SUBMITTED"
    data['ticket_type'] = ticket_type
    data = preprocess(data, registration_event_schema)
    res = mongo_register_event.insert_one({**data, "_id": data['member_id'] + "_" + data['event_id']})

    result = {"id": res.inserted_id, "result": "inserted"}

    return result


def send_request(amount,
                 description,
                 email=None,
                 mobile=None, ):
    request = {
        "merchant_id": MMERCHANT_ID,
        "amount": amount,
        "callback_url": 'https://www.w3schools.com/git/git_ignore.asp?remote=github',
        "description": description,
        "metadata": {
            "mobile": mobile,
            "email": email
        }
    }
    result = requests.post(url="https://api.zarinpal.com/pg/v4/payment/request.json",
                           json=request
                           )
    if result.status_code == 200:
        return result.json()['data']
    else:
        raise PaymentException()


def verify(amount, authority):
    request = {
        "merchant_id": MMERCHANT_ID,
        "amount": amount,
        "authority": authority,
    }
    result = requests.post(url="https://api.zarinpal.com/pg/v4/payment/verify.json",
                           json=request
                           )
    if result.status_code == 200:
        result = result.json()
    else:
        return 'Error'

    if result['data'] not in ['null', None, []]:
        if result['data']['code'] == 100:
            return {"status": 100, 'RefID': str(result['data']['ref_id'])}
        elif result['data']['code'] == 101:
            return {"status": 101, 'submitted': str(result['data']['ref_id'])}
    else:
        raise PaymentException()


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


class PaymentException(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(PaymentException, self).__init__(message="Payment exception ",
                                               error_code=error_code_base + 106,
                                               persian_massage="پرداخت ناموفق بود .")


class DuplicatedDiscountCode(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(DuplicatedDiscountCode, self).__init__(message="discountcode is already exist ",
                                                     error_code=error_code_base + 107,
                                                     persian_massage="کد تخفیفی با این مشخصات وجود دارد.")


class InvalidDiscountCode(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(InvalidDiscountCode, self).__init__(message="discountcode is not exist ",
                                                  error_code=error_code_base + 108,
                                                  persian_massage="کد تخفیفی با این مشخصات وجود ندارد.")


class CapacityDiscountCode(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(CapacityDiscountCode, self).__init__(message="discount code doesn't have capacity ",
                                                   error_code=error_code_base + 109,
                                                   persian_massage="ظرفیت کد تخفیف تمام شده است.")


class FinishTime(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(FinishTime, self).__init__(message="registration time was finished",
                                         error_code=error_code_base + 109,
                                         persian_massage="زمان ثبت نام تمام شده است.")
