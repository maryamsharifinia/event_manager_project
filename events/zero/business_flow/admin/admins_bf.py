import datetime

from events.zero.utils.utils import *
from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import events as service

# noinspection PyMethodMayBeStatic
from helpers.io_helpers import *


class AdminBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(AdminBusinessFlowManager, self).__init__(service.service_name)

        self.cfg_helper = ConfigHelper()
        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])
        self.index_name_discount_code = self.create_index(
            self.cfg_helper.get_config(service.service_name)["index_name_discount_code"])
        self.index_register = self.create_index(
            self.cfg_helper.get_config(service.service_name)["index_name_register_event"])

    # noinspection PyUnusedLocal
    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]
        data = data['data']

        if method == "select_in_registration":
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))

            query = preprocess_schema(data, schema=service.event_schema)
            total = len(list(self.index_register.find(query)))

            search_result = list(
                self.index_register.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))

            results = {"total": total, "result": list(search_result)}
        elif method == "select_in_events":
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))

            query = preprocess_schema(data, schema=service.event_schema)
            total = len(list(self.index.find(query)))

            search_result = list(
                self.index.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))
            for item in search_result:
                if item["image"] not in ['null', None, "None"]:
                    item["image"] = self.serve_file(service.service_name, item["image"])

            results = {"total": total, "result": list(search_result)}
        elif method == 'select_my_event':

            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))
            data["memebr_id"] = member["_id"]
            query = preprocess_schema(data, schema=service.event_schema)
            total = len(list(self.index.find(query)))

            search_result = list(
                self.index.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))
            for item in search_result:
                if item["image"] not in ['null', None, "None"]:
                    item["image"] = self.serve_file(service.service_name, item["image"])

            results = {"total": total, "result": list(search_result)}

        elif method == 'select_all_admins_event':
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))
            query = preprocess_schema(data, schema=service.event_schema)
            total = len(list(self.index.find(query)))
            search_result = list(
                self.index.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))
            for item in search_result:
                if item["image"] not in ['null', None, "None"]:
                    item["image"] = self.serve_file(service.service_name, item["image"])

            results = {"total": total, "result": list(search_result)}

        elif method == 'select_discount_code':
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))

            query = preprocess_schema(data, schema=service.discount_code_schema)
            total = len(list(self.index_name_discount_code.find(query)))

            search_result = list(
                self.index_name_discount_code.find().skip(from_value).limit(to_value - from_value).sort(sort,
                                                                                                        sort_type))

            results = {"total": total, "result": list(search_result)}
        else:
            raise PermissionError()

        return {"results": results}

    def insert_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
        data = data['data']
        method = request["method"]

        if method == "insert_event":
            check_required_key(["name",
                                "registration_start_date",
                                "registration_end_date",
                                "start_date",
                                "end_date",
                                "hours",
                                "subject",
                                "teacher_name",
                                "platform",
                                "image"], data)
            query = get_insert_check_query(data, service.event_schema)
            if len(list(self.index.find(query))) != 0:
                raise DuplicatedEvent()
            if 'image' in data:
                image_id = self.insert_file(service.service_name, data['image']['file_content'],
                                            data['image']['file_type'],
                                            member["_id"] + "@" + datetime.datetime.now().strftime(
                                                "%Y%m%d_%H:%M:%S.%f"))
                image_id = image_id.inserted_id
            else:
                image_id = None
            data['member_id'] = member["_id"]
            data = check_full_schema(data, service.event_schema)
            data = preprocess(data, schema=service.event_schema)
            data['image'] = image_id

            self.index.insert_one({**data, "_id": member["_id"] + "@" + datetime.datetime.now().strftime(
                "%Y%m%d_%H:%M:%S.%f")})
            results = {"status": "inserted_event"}
        elif method == "insert_discount_code":
            check_required_key(["discount_code",
                                "event_id",
                                "number_of_use",
                                "ticket_type",
                                "start_date",
                                "end_date",
                                "how_apply", ], data)
            query = get_insert_check_query(data, service.discount_code_schema)
            event = list(self.index.find({'_id': data['event_id']}))
            if len(event) == 0:
                raise InvalidInputField("event_id")
            if len(list(self.index_name_discount_code.find(query))) != 0:
                raise DuplicatedDiscountCode()
            data['event_name'] = event[0]['name']
            data = check_full_schema(data, service.discount_code_schema)
            data = preprocess(data, schema=service.discount_code_schema)

            self.index_name_discount_code.insert_one(
                {**data, "_id": member["_id"] + "@" + datetime.datetime.now().strftime(
                    "%Y%m%d_%H:%M:%S.%f")})
            results = {"status": "inserted_discount_code"}
        else:
            raise PermissionError()

        return {"results": results}

    def delete_business_flow(self, data, request, member, params=None):
        raise PermissionError()

    def update_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
        data = data['data']
        method = request["method"]

        if method == "update_event":
            if 'image' in data:
                image_id = self.insert_file(service.service_name, data['image']['file_content'],
                                            data['image']['file_type'],
                                            member["_id"] + "@" + datetime.datetime.now().strftime(
                                                "%Y%m%d_%H:%M:%S.%f"))
                image_id = image_id.inserted_id
                data['image'] = image_id

            check_schema(data, service.event_schema)
            data = preprocess(data, schema=service.event_schema)

            result = update_event(self.index, data)
            return result
