import datetime
import time

from helpers.business_flow_helpers import BusinessFlow
from helpers.config_helper import ConfigHelper
from members import send_email
import traceback as tb


class SendEmail(BusinessFlow):
    def __init__(self, delay, broker_type, emails, event_registration, members, events):
        super(SendEmail, self).__init__("EVENTS")
        self.delay = int(delay)
        self.broker_type = broker_type
        self.index_name_email = self.create_index(emails)
        self.index_name_event_registration = self.create_index(event_registration)
        self.index_name_events = self.create_index(events)
        self.index_name_members = BusinessFlow("MEMBERS").create_index(members)

    def loop(self):
        while True:

            try:

                self.run()
                time.sleep(self.delay)

            except  Exception as e:
                tb.print_exc()
                time.sleep(3600)

    def run(self):
        res = list(self.index_name_email.find({"status": "undone", "is_active": True, }))
        for i in res:
            if i['receivers'] == 'event_participants':
                event_registration = list(self.index_name_event_registration.find({'event_id': i['event_id']}))
                if i['send_time'] == 'now':
                    for registration in event_registration:
                        email = list(self.index_name_members.find({'_id': registration['member_id']}))[0]['email']
                        send_email({"email": email, "content": i["content"]}, f" رویداد{i['event_name']}")

                    myquery = {"_id": i["_id"]}
                    newvalues = {"$set": {"status": "done"}}

                    self.index_name_email.update_one(myquery, newvalues)
                elif i['send_time'] == 'now':
                    now = datetime.datetime.now().strftime("%Y/%m/%d")
                    send_date = i['send_date']
                    if now == send_date:
                        for registration in event_registration:
                            email = list(self.index_name_members.find({'_id': registration['member_id']}))[0]['email']
                            send_email({"email": email, "content": i["content"]}, f" رویداد{i['event_name']}")

                        myquery = {"_id": i["_id"]}
                        newvalues = {"$set": {"status": "done"}}

                        self.index_name_email.update_one(myquery, newvalues)

                elif i['send_time'] == 'before_event':
                    start_date = list(self.index_name_events.find({"_id": i['event_id']}))[0]['start_date'][:10]
                    now = (datetime.datetime.now() - datetime.timedelta(1)).strftime("%Y/%m/%d")
                    if now == start_date:
                        for registration in event_registration:
                            email = list(self.index_name_members.find({'_id': registration['member_id']}))[0]['email']
                            send_email({"email": email, "content": i["content"]}, f" رویداد{i['event_name']}")

                        myquery = {"_id": i["_id"]}
                        newvalues = {"$set": {"status": "done"}}

                        self.index_name_email.update_one(myquery, newvalues)


if __name__ == "__main__":
    while True:
        try:
            cfg_helper = ConfigHelper()

            broker_type = cfg_helper.get_config("DEFAULT")["broker_type"]
            event_registration = cfg_helper.get_config("EVENTS")["index_name_register_event"]
            emails = cfg_helper.get_config("EVENTS")["index_name_emails"]
            events = cfg_helper.get_config("EVENTS")["index_name"]
            members = cfg_helper.get_config("MEMBERS")["index_name"]

            worker = SendEmail(delay=24 * 60 * 60, broker_type=broker_type,
                               emails=emails, event_registration=event_registration,
                               members=members, events=events)

            worker.loop()
        except Exception as e:
            tb.print_exc()
            time.sleep(10)
