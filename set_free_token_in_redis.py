from helpers.config_helper import ConfigHelper
from walrus import *

cfg_helper = ConfigHelper()
redis_host = cfg_helper.get_config("DB_API")["redis_host"]
redis_port = cfg_helper.get_config("DB_API")["redis_port"]
redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

free_member_id = cfg_helper.get_config("MEMBERS")["free_member_id"]
free_token = cfg_helper.get_config("MEMBERS")["free_token"]
free_ttl = cfg_helper.get_config("MEMBERS")["free_ttl"]

cache_db = Database(redis_host, redis_port, redis_db_number)
_cache = cache_db.cache("authorization_cache")

_cache.set(free_member_id, json.dumps({"token": free_token, "member_type": "FREE", "permitted_methods": "CLUB"}),
           free_ttl)
free_data = {"_id": "free_id",
             "national_id": "0000000000",
             "gender": "1",
             "permitted_methods": "CLUB",
             "pass_salt": "null",
             "category": "FREE",
             "user": "test",
             }
import pymongo
mongo = pymongo.MongoClient("mongodb://localhost:27017/").myclient["members"]
mycol = mongo["member_info"]

x = mycol.insert_one(free_data)
