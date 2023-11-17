from helpers.config_helper import ConfigHelper
from helpers.io_helpers import RequiredFieldError, UserInputError


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


class DuplicatedEvent(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(DuplicatedEvent, self).__init__(message="Member is already exist ",
                                              error_code=error_code_base + 101,
                                              persian_massage="رویدادی با این مشخصات وجود دارد.")
