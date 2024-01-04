import json

event_schema = {"broker_type": {"_type": str, "_null_value": "null", "_check_in_insert": True},
                "name": {"_type": str, "_null_value": "null", "_check_in_insert": True},
                "is_active": {"_type": str, "_null_value": "TRUE", "_check_in_insert": False},
                "external_links": {"_type": str, "_null_value": "null", "_check_in_insert": False},
                "member_id": {"_type": str, "_null_value": "null", "_check_in_insert": False},
                "ticket_type": {"_type": dict, "_null_value": json.dumps(
                    {"1": {"cost": 0,
                           "name": 0,
                           "participants": 0,
                           "max_participants": 0,
                           "start_date": "1970/01/01 00:00:00.000000",
                           "end_date": "1970/01/01 00:00:00.000000"
                           }}),
                                "_check_in_insert": False},
                "registration_start_date": {"type": "date", "_type": str, "_null_value": "1970/01/01 00:00:00.000000",
                                            "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS", "_check_in_insert": False},
                "registration_end_date": {"type": "date", "_type": str, "_null_value": "1970/01/01 00:00:00.000000",
                                          "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS", "_check_in_insert": False},
                "start_date": {"_type": str, "_null_value": "1970/01/01 00:00:00.000000",
                               "_check_in_insert": False},
                "end_date": {"_type": str, "_null_value": "1970/01/01 00:00:00.000000",
                             "_check_in_insert": False},
                "hours": {"_type": int, "_null_value": 0, "_check_in_insert": True},
                "participants": {"_type": int, "_null_value": 0, "_check_in_insert": False},
                "subject": {"_type": str, "_null_value": "null", "_check_in_insert": True},
                "teacher_name": {"_type": str, "_null_value": "null", "_check_in_insert": True},
                "location": {"_type": str, "_null_value": "null", "_check_in_insert": False},
                "platform": {"_type": str, "_null_value": "null", "_check_in_insert": True},
                "explanations": {"_type": str, "_null_value": "null", "_check_in_insert": False},
                "image": {"_type": str, "_null_value": "null", "_check_in_insert": False},
                "DC_CREATE_TIME": {"_type": str, "_null_value": "1970/01/01 00:00:00.000000",
                                   "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS",
                                   "_check_in_insert": False},
                }
registration_event_schema = {
    "broker_type": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": True},
    "event_id": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": True},
    "event_name": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": False},
    "member_id": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": True},
    "first_name": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": False},
    "last_name": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": False},
    "national_id": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": False},
    "registration_date": {"type": "date", "_type": str, "_null_value": "1970/01/01 00:00:00.000000",
                          "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS", "_check_in_insert": False},
    "status": {"type": "keyword", "_type": str, "_null_value": "SUBMITTED", "_check_in_insert": False},
    "DC_CREATE_TIME": {"type": "date", "_type": str, "_null_value": "1970/01/01 00:00:00.000000",
                       "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS",
                       "_check_in_insert": False},
}


comment_event_schema = {
    "member_id": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": True},
    "event_id": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": True},
    "comment": {"type": "keyword", "_type": str, "_null_value": "null", "_check_in_insert": False},
}