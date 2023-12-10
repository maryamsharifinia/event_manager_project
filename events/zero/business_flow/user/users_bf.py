import json

from events.zero.utils.utils import *
from events.zero.utils.utils import register_event as reg
from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import events as service
from helpers.io_helpers import *


class UserBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(UserBusinessFlowManager, self).__init__(service.service_name)
        self.cfg_helper = ConfigHelper()

        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])
        self.index_register = self.create_index(
            self.cfg_helper.get_config(service.service_name)["index_name_register_event"])

    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        method = request["method"]

        method = request["method"]
        data = data["data"]
        if method == "select_event":
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))

            query = preprocess_schema(data, schema=service.event_schema)
            total = len(list(self.index.find(query)))

            search_result = list(self.index.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))
            for item in search_result:
                if item["image"] not in ['null', None, "None"]:
                    item["image"] = self.serve_file(service.service_name, item["image"])

            results = {"total": total, "result": list(search_result)}
        return {}

    def insert_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
        data = data["data"]
        method = request["method"]

        if method == "register_event":
            if "_id" not in data.keys():
                raise RequiredFieldError("_id")
            event_id = data['_id']
            event_info = get_event_by_id(self.mongo, event_id)
            ticket_types = event_info['ticket_type']

            query = get_insert_check_query({"event_id": event_id, "member_id": member["_id"]},
                                           service.registration_event_schema)
            if len(list(self.index_register.find(query))) != 0:
                raise DuplicatedRegister()

            ticket_type = "1" if "ticket_type" not in data.keys() else data["ticket_type"]

            if "participants" not in ticket_types[ticket_type]:
                ticket_types[ticket_type]['participants'] = 0

            if ticket_types[ticket_type]['participants'] >= ticket_types[ticket_type]['max_participants']:
                raise CapacityError()

            cost = ticket_types[ticket_type]['cost']

            name = event_info['name']
            mobile = member['phone']
            email = member['email']

            if cost > 0:
                return send_request(amount=cost,
                                    description=f' خرید دوره{name}',
                                    email=email,
                                    mobile=mobile)


            else:
                register_event = reg(event_info=event_info, mongo_register_event=self.index_register,
                                     member=member, registration_event_schema=service.registration_event_schema)
                myquery = {"_id": event_id}
                ticket_types[ticket_type]['participants'] += 1
                newvalues = {"$set": {"ticket_type": ticket_types}}
                self.index.update_one(myquery, newvalues)
            return register_event

        elif method == "verify_payment":
            event_id = data['_id']
            event_info = get_event_by_id(self.mongo, event_id)
            ticket_types = json.loads(event_info['ticket_type'])
            ticket_type = "1" if "ticket_type" not in data.keys() else data["ticket_type"]

            if "participants" not in ticket_types[ticket_type]:
                ticket_types[ticket_type]['participants'] = 0
            if ticket_types[ticket_type]['participants'] >= ticket_types[ticket_type]['max_participants']:
                raise CapacityError()

            cost = ticket_types[ticket_type]['cost']

            res = verify(cost, data['authority'])
            status = res['status']
            if status == 100 or status == 101:
                query = get_insert_check_query({"event_id": event_id, "member_id": member["_id"]},
                                               service.registration_event_schema)
                if len(list(self.index_register.find(query))) != 0:
                    raise DuplicatedRegister()
                register_event = reg(event_info=event_info, mongo_register_event=self.index_register,
                                     member=member, registration_event_schema=service.registration_event_schema)
                register_event = {**register_event, **res}
                myquery = {"_id": event_id}
                ticket_types[ticket_type]['participants'] += 1
                newvalues = {"$set": {"ticket_type": ticket_types}}
                self.index.update_one(myquery, newvalues)
            else:
                raise PaymentFailed()
            return register_event

        else:
            raise PermissionError()

    def delete_business_flow(self, data, request, member, params=None):
        raise PermissionError()

    def update_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()

        if request["method"] == "update":
            pass
        else:
            raise PermissionError()

        return []
