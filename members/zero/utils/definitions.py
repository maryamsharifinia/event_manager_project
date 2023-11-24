clubmembers_schema = {
    "first_name": {"_type": str, "_null_value": "null", "_check_in_insert": False},
    "last_name": {"_type": str, "_null_value": "null", "_check_in_insert": False},
    "permitted_methods": {"_type": str, "_null_value": "CLUB",
                          "_check_in_insert": False},

    "national_id": {"_type": str, "_null_value": "null", "_check_in_insert": True},
    "student_number": {"_type": str, "_null_value": "null", "_check_in_insert": True},
    "gender": {"_type": str, "_null_value": "null",
               "_check_in_insert": False},
    "category": {"_type": str, "_null_value": "MEMBER", "_check_in_insert": False},
    "user": {"_type": str, "_null_value": "null", "_check_in_insert": True},
    "pass_salt": {"_type": str, "_null_value": "null", "_check_in_insert": False},
    "pass_hash": {"_type": str, "_null_value": "null", "_check_in_insert": False},
    "phone": {"_type": str, "_null_value": "null", "_check_in_insert": True},
    "email": {"_type": str, "_null_value": "null", "_check_in_insert": False},
    "verify_email": {"_type": str, "_null_value": "FALSE", "_check_in_insert": False},
    "verify_phone": {"_type": str, "_null_value": "FALSE", "_check_in_insert": False},
    "registration_date": {"_type": str, "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS",
                          "_null_value": "1970/01/01 00:00:00.000000",
                          "_check_in_insert": False},
    "birth_date": {"_type": str, "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS",
                   "_null_value": "1970/01/01 00:00:00.000000",
                   "_check_in_insert": False},
    "DC_CREATE_TIME": {"_type": str, "format": "8yyyy/MM/dd HH:mm:ss.SSSSSS",
                       "_null_value": "1970/01/01 00:00:00.000000",
                       "_check_in_insert": False},
}
