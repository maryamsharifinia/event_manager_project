import datetime
import json

from events.zero.utils.utils import *
from events.zero.utils.utils import register_event as reg
from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper

import events as service
from helpers.io_helpers import *
from members import transaction_schema


class UserBusinessFlowManager(BusinessFlow):
    def __init__(self, ):
        super(UserBusinessFlowManager, self).__init__(service.service_name)
        self.cfg_helper = ConfigHelper()

        self.index = self.create_index(self.cfg_helper.get_config(service.service_name)["index_name"])
        self.index_register = self.create_index(
            self.cfg_helper.get_config(service.service_name)["index_name_register_event"])

        self.index_comment = self.create_index(
            self.cfg_helper.get_config(service.service_name)["index_name_comments"])

        self.index_transactions = self.create_index(self.cfg_helper.get_config("MEMBERS")["transactions_index_name"])
        self.index_name_discount_code = self.create_index(
            self.cfg_helper.get_config(service.service_name)["index_name_discount_code"])

    def select_business_flow(self, data, request, member, params=None):
        self.get_mongo_connection()
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


            results = {"total": total, "result": list(search_result)}
        elif method == "select_ticket":
            query = {"person_id": member["id"]}
            tickets = list(self.tickets_collection.find(query))
            # Process the retrieved tickets as needed
            results = {"result": tickets}
        elif method == "select_all_events":
            query = {"person_id": member["id"]}
            events = list(self.events_collection.find(query))
            # Process the retrieved events as needed
            results = {"result": events}
        if method == "select_my_ticket":
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))
            data["memebr_id"] = member["_id"]
            query = preprocess_schema(data, schema=service.registration_event_schema)
            total = len(list(self.index_register.find(query)))

            search_result = list(
                self.index_register.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))

            results = {"total": total, "result": list(search_result)}


        if method == "select_events_comment":
            sort = "DC_CREATE_TIME"
            sort_type = 1
            if "sort" in data:
                sort = data["sort"]["name"]
                sort_type = data["sort"]["type"]
            from_value = int(data.get('from', 0))
            to_value = int(data.get('to', 10))
            data["event_id"] = events["_id"]
            query = preprocess_schema(data, schema=service.comment_event_schema)
            total = len(list(self.index_register.find(query)))
            search_result = list(
                self.index_register.find().skip(from_value).limit(to_value - from_value).sort(sort, sort_type))
            results = {"total": total, "result": list(search_result)}


        return results

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

            now = datetime.datetime.now()
            start_time = datetime.datetime.strptime(event_info['registration_start_date'], "%Y/%m/%d %H:%M:%S.%f")
            end_time = datetime.datetime.strptime(event_info['registration_end_date'], "%Y/%m/%d %H:%M:%S.%f")
            if now > end_time or now < start_time:
                raise FinishTime()

            if "discount_code" in data:
                discount_code = data['discount_code']
                discount_code_data = list(
                    self.index_name_discount_code.find({"discount_code": discount_code, "event_id": event_id}))
                if len(discount_code_data) == 0:
                    raise InvalidDiscountCode()
                if len(discount_code_data[0]['members']) >= discount_code_data[0]['number_of_use']:
                    raise CapacityDiscountCode()
                start_time = datetime.datetime.strptime(discount_code_data[0]['start_date'], "%Y/%m/%d %H:%M:%S.%f")
                end_time = datetime.datetime.strptime(discount_code_data[0]['end_date'], "%Y/%m/%d %H:%M:%S.%f")
                if now > end_time or now < start_time:
                    raise FinishTime()
                cost = ticket_types[ticket_type]['cost'] * (
                        (100 - discount_code_data[0]['how_apply']['percentage']) / 100) - \
                       discount_code_data[0]['how_apply']['amount']
                event_info['discount_code'] = discount_code
            else:
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
                if "discount_code" in data:
                    myquery = {"_id": discount_code_data[0]["_id"]}
                    discount_code_data[0]['members'].append(member["_id"])
                    newvalues = {"$set": {"members": discount_code_data[0]['members']}}
                    self.index_name_discount_code.update_one(myquery, newvalues)

            return register_event

        elif method == "insert_comment":
            comment = {
                "event_id": data['event_id'],
                "member_id": data['member_id'],
                "text_comment": data['comment']
            }
            inserted_comment = self.index_comment.insert_one(comment)
            return inserted_comment.inserted_id

        elif method == "verify_payment":
            check_required_key(["_id", 'authority'], data)
            event_id = data['_id']
            authority = data['authority']
            event_info = get_event_by_id(self.mongo, event_id)
            ticket_types = json.loads(event_info['ticket_type'])
            ticket_type = "1" if "ticket_type" not in data.keys() else data["ticket_type"]

            if "participants" not in ticket_types[ticket_type]:
                ticket_types[ticket_type]['participants'] = 0
            if ticket_types[ticket_type]['participants'] >= ticket_types[ticket_type]['max_participants']:
                raise CapacityError()

            if "discount_code" in data:
                discount_code = data['discount_code']
                discount_code_data = list(
                    self.index_name_discount_code.find({"discount_code": discount_code, "event_id": event_id}))

                cost = ticket_types[ticket_type]['cost'] * (
                        (100 - discount_code_data[0]['how_apply']['percentage']) / 100) - \
                       discount_code_data[0]['how_apply']['amount']
                event_info['discount_code'] = discount_code
            else:
                cost = ticket_types[ticket_type]['cost']

            res = verify(cost, authority)
            status = res['status']
            if status == 100 or status == 101:
                query = get_insert_check_query({"event_id": event_id, "member_id": member["_id"]},
                                               service.registration_event_schema)
                if len(list(self.index_register.find(query))) != 0:
                    raise DuplicatedRegister()
                register_event = reg(event_info=event_info, mongo_register_event=self.index_register,
                                     member=member, registration_event_schema=service.registration_event_schema)
                # update members
                register_event = {**register_event, **res}
                myquery = {"_id": event_id}
                ticket_types[ticket_type]['participants'] += 1
                newvalues = {"$set": {"ticket_type": ticket_types}}
                self.index.update_one(myquery, newvalues)

                # insert transaction
                _type = 'register_event'
                doc = check_full_schema({**member, "authority": authority,
                                         "type": _type,
                                         "payment": cost,
                                         "member_id": member["_id"]}, transaction_schema)
                doc = preprocess(doc, transaction_schema)
                self.index_transactions.insert_one({**doc, "_id": doc['member_id'] + "_" + doc['authority']})

                # update discount_code
                if "discount_code" in data:
                    myquery = {"_id": discount_code_data[0]["_id"]}
                    discount_code_data[0]['members'].append(member["_id"])
                    newvalues = {"$set": {"members": discount_code_data[0]['members']}}
                    self.index_name_discount_code.update_one(myquery, newvalues)
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
