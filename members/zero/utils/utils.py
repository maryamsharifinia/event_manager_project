import base64
import json
import re
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from hashlib import sha256, md5
from uuid import uuid4

import requests

from helpers.config_helper import ConfigHelper
from helpers.io_helpers import MemberNotFoundError, UserInputError, RequiredFieldError

MMERCHANT_ID = '1344b5d4-0048-11e8-94db-005056a205be'
ZARINPAL_WEBSERVICE = 'https://www.zarinpal.com/pg/services/WebGate/wsdl'


def get_member(mongo, request_sender_id):
    query = {"_id": request_sender_id}

    search_result = list(mongo.mydb["member_info"].find(query))

    if len(search_result) != 1:
        raise MemberNotFoundError()

    return search_result[0]


def get_member_by_username(mongo, username, index_name):
    query = {"user": username}
    search_result = list(mongo.mydb[index_name].find(query))

    request_sender_member = {"_source": None, "_id": None}

    if len(search_result) == 1:
        request_sender_member = {"_source": search_result[0],
                                 "_id": search_result[0]["_id"]}

    return request_sender_member


def check_password(password, member):
    real_hash = member["_source"]["pass_hash"]

    bytes_obj = (password + member["_source"]["pass_salt"]).encode("utf-16-le")

    sha_digest = sha256(bytes_obj).digest()
    pass_hash = base64.b64encode(sha_digest)

    if pass_hash.decode() == real_hash:
        return True
    else:
        return False


def create_salt_and_hash(md5_password):
    salt = str(uuid4())

    bytes_obj = (md5_password + salt).encode("utf-16-le")

    sha_digest = sha256(bytes_obj).digest()
    _hash = base64.b64encode(sha_digest).decode()

    return salt, _hash


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


def update_member(mongo, data):
    _id = data["_id"]
    del data["_id"]

    blocked_fields = ["national_id", "is_active"]

    data_keys = list(data.keys())
    for k in data_keys:
        if k in blocked_fields:
            del data[k]

    if "permitted_methods" in data.keys() and data["permitted_methods"] != "CLUB":
        data["category"] = "ADMIN"
    elif "permitted_methods" in data.keys() and data["permitted_methods"] == "CLUB":
        data["category"] = "MEMBER"

    myquery = {"_id": _id}
    newvalues = {"$set": {**data}}

    update_result = mongo.update_one(myquery, newvalues)

    result = {"id": _id, "result": update_result.raw_result}

    return result


def change_password(data, member, mongo):
    if member["_id"] != data["member_id"]:
        raise PermissionError()

    old_password = data["old_password"]
    md5_password = md5(old_password.encode()).hexdigest().upper()

    login_member = {"_source": member, "_id": member["_id"]}
    if not check_password(password=md5_password, member=login_member) \
            and not check_password(password=old_password, member=login_member):
        raise InvalidCurrentPassword()

    update_result = set_new_password(new_password=data["new_password"], member_id=member["_id"],
                                     mongo=mongo)

    result = {"id": update_result["_id"], "result": update_result["result"]}
    return result


def set_new_password(new_password, member_id, mongo):
    if len(re.findall('^(?=.*\d)(?=.*[A-Z])(?=.*[a-z])[A-Za-z0-9@#$%^&+=\!\*]{8,}$', new_password)) == 0:
        raise InvalidPasswordStructure()

    md5_password = md5(new_password.encode()).hexdigest().upper()
    pass_salt, pass_hash = create_salt_and_hash(md5_password)
    update_body = {
        "pass_salt": pass_salt,
        "pass_hash": pass_hash

    }
    myquery = {"_id": member_id}
    newvalues = {"$set": {**update_body}}

    update_result = mongo.update_one(myquery, newvalues)

    update_result = {"_id": member_id, "result": update_result.raw_result}
    return update_result


def send_email(data, display_name):
    smtp_server = "smtp.gmail.com"
    smtp_password = "yqjn nssh cykb ztej"
    smtp_email = "scientificsocietyiust@gmail.com"

    target_email = data["email"]
    if target_email is None or target_email == "" or len(re.findall("^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$",
                                                                    target_email)) == 0:
        raise Exception("EMAIL_NOT_SENT: INVALID EMAIL ADDRESS")

    with smtplib.SMTP_SSL(host=smtp_server, port=465, timeout=10) as server:
        server.login(smtp_email, smtp_password)

        name = "انجمن علمی دانشگاه علم و صنعت"
        content = data["content"]

        from_header = Header(display_name, "utf-8")
        from_header.append("<%s>" % smtp_email, "ascii")

        msg = MIMEMultipart('alternative')
        msg.set_charset('utf-8')
        msg['Subject'] = Header(name, 'utf-8')
        msg["From"] = from_header
        msg['To'] = "<%s>" % target_email

        html = get_email_body(content, name)

        mime_text = MIMEText(html, 'html', "utf-8")

        msg.attach(mime_text)

        response = server.sendmail(from_addr=smtp_email, to_addrs=target_email, msg=msg.as_string())

        if response == {}:
            return {"result": "EMAIL SENT", "sent": True, "code": 200}
        else:
            raise Exception("EMAIL_NOT_SENT")


def get_email_body(content, broker_name):
    return """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" 
        "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns=" http://www.w3.org/1999/xhtml">

<head>
    <!-- If you delete this tag, the sky will fall on your head -->
    <meta name="viewport" content="width=device-width" />

    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>{}</title>""".format(broker_name) + """<style>
        /* ------------------------------------- 
GLOBAL 
------------------------------------- */
        * {
            margin: 0;
            padding: 0;
        }

        * {
            font-family: "tahoma", "Helvetica Neue", "Helvetica", Helvetica, Arial, sans-serif;
        }

        img {
            max-width: 100%;
        }

        .collapse {
            margin: 0;
            padding: 0;
        }

        body {
            -webkit-font-smoothing: antialiased;
            -webkit-text-size-adjust: none;
            width: 100% !important;
            height: 100%;
        }


        /* ------------------------------------- 
ELEMENTS 
------------------------------------- */
        a {
            color: #2BA6CB;
        }

        .btn {
            width: 94%;
            text-decoration: none;
            color: #FFF;
            border: 1px solid #6C757D;
            background-color: #6C757D;
            border-radius: 5px;
            padding: 10px 16px;
            font-weight: 300;
            text-align: center;
            cursor: pointer;
            display: inline-block;
        }

        .btn:hover {
            text-decoration: none;
            border: 1px solid #6C757D;
            color: #6C757D;
            background-color: #fff;
            border-radius: 5px;
            padding: 10px 16px;
            font-weight: 300;
            text-align: center;
            transition: 0.2s;
            box-shadow: 2px 3px 10px 0px gray;
            cursor: pointer;
            display: inline-block;
        }

        p.callout {
            padding: 15px;
            background-color: #dbf1ff;
            margin-bottom: 15px;
            border-radius: 8px;
        }


        table.social {
            /* padding:15px; */
            background-color: #ebebeb;
            border-radius: 8px;

        }

        .social .soc-btn {
            border-radius: 4px;
            padding: 3px 7px;
            font-size: 12px;
            margin-bottom: 10px;
            text-decoration: none;
            color: #FFF;
            font-weight: bold;
            display: block;
            text-align: center;
        }

        a.fb {
            background-color: #3B5998 !important;
        }

        a.tw {
            background-color: #1daced !important;
        }

        a.gp {
            background: linear-gradient(45deg, #405de6, #5851db, #833ab4, #c13584, #e1306c, #fd1d1d) !important;
        }

        a.ms {
            background-color: #000 !important;
        }

        .sidebar .soc-btn {
            display: block;
            width: 100%;
        }

        /* ------------------------------------- 
HEADER 
------------------------------------- */
        table.head-wrap {
            width: 100%;
        }

        .header.container table td.logo {
            padding: 15px;
        }

        .header.container table td.label {
            padding: 15px;
            padding-left: 0px;
        }


        /* ------------------------------------- 
BODY 
------------------------------------- */
        table.body-wrap {
            width: 100%;
        }


        /* ------------------------------------- 
FOOTER 
------------------------------------- */
        table.footer-wrap {
            width: 100%;
            clear: both !important;
        }

        .footer-wrap .container td.content p {
            border-top: 1px solid rgb(215, 215, 215);
            padding-top: 15px;
        }

        .footer-wrap .container td.content p {
            font-size: 10px;
            font-weight: bold;

        }


        /* ------------------------------------- 
TYPOGRAPHY 
------------------------------------- */
        h1,
        h2,
        h3,
        h4,
        h5,
        h6 {
            font-family: "HelveticaNeue-Light", "Helvetica Neue Light", "Helvetica Neue", Helvetica, Arial, 
            "Lucida Grande", sans-serif;
            line-height: 1.1;
            margin-bottom: 15px;
            color: #000;
        }

        h1 small,
        h2 small,
        h3 small,
        h4 small,
        h5 small,
        h6 small {
            font-size: 60%;
            color: #6f6f6f;
            line-height: 0;
            text-transform: none;
        }

        h1 {
            font-weight: 200;
            font-size: 44px;
        }

        h2 {
            font-weight: 200;
            font-size: 37px;
        }

        h3 {
            font-weight: 500;
            font-size: 27px;
        }

        h4 {
            font-weight: 500;
            font-size: 23px;
        }

        h5 {
            font-weight: 900;
            font-size: 17px;
        }

        h6 {
            font-weight: 900;
            font-size: 14px;
            text-transform: uppercase;
            color: #444;
        }

        .collapse {
            margin: 0 !important;
        }

        p,
        ul {
            margin-bottom: 10px;
            font-weight: normal;
            font-size: 14px;
            line-height: 1.6;
        }

        p.lead {
            font-size: 17px;
        }

        p.last {
            margin-bottom: 0px;
        }

        ul li {
            margin-left: 5px;
            list-style-position: inside;
        }

        /* ------------------------------------- 
SIDEBAR 
------------------------------------- */
        ul.sidebar {
            background: #ebebeb;
            display: block;
            list-style-type: none;
        }

        ul.sidebar li {
            display: block;
            margin: 0;
        }

        ul.sidebar li a {
            text-decoration: none;
            color: #666;
            padding: 10px 16px;
            /* font-weight:bold; */
            margin-right: 10px;
            /* text-align:center; */
            cursor: pointer;
            border-bottom: 1px solid #777777;
            border-top: 1px solid #FFFFFF;
            display: block;
            margin: 0;
        }

        ul.sidebar li a.last {
            border-bottom-width: 0px;
        }

        ul.sidebar li a h1,
        ul.sidebar li a h2,
        ul.sidebar li a h3,
        ul.sidebar li a h4,
        ul.sidebar li a h5,
        ul.sidebar li a h6,
        ul.sidebar li a p {
            margin-bottom: 0 !important;
        }



        /* --------------------------------------------------- 
RESPONSIVENESS
Nuke it from orbit. It's the only way to be sure. 
------------------------------------------------------ */

        /* Set a max-width, and make it display as block so it will automatically stretch to that width, but will also
         shrink down on a phone or something */
        .container {
            display: block !important;
            max-width: 600px !important;
            margin: 0 auto !important;
            /* makes it centered */
            clear: both !important;
        }

        /* This should also be a block element, so that it will fill 100% of the .container */
        .content {
            padding: 15px;
            max-width: 600px;
            margin: 0 auto;
            display: block;
        }

        /* Let's make sure tables in the content area are 100% wide */
        .content table {
            width: 100%;
        }


        /* Odds and ends */
        .column {
            width: 300px;
            float: left;
        }

        .column tr td {
            padding: 15px;
        }

        .column-wrap {
            padding: 0 !important;
            margin: 0 auto;
            max-width: 600px !important;
        }

        .column table {
            width: 100%;
        }

        .social .column {
            width: 280px;
            min-width: 279px;
            float: left;
        }

        /* Be sure to place a .clear element after each set of columns, just to be safe */
        .clear {
            display: block;
            clear: both;
        }


        /* ------------------------------------------- 
PHONE
For clients that support media queries.
Nothing fancy. 
-------------------------------------------- */
        @media only screen and (max-width: 600px) {

            a[class="btn"] {
                display: block !important;
                margin-bottom: 10px !important;
                background-image: none !important;
                margin-right: 0 !important;
            }

            div[class="column"] {
                width: auto !important;
                float: none !important;
            }

            table.social div[class="column"] {
                width: auto !important;
            }

        }
    </style>
</head>

<body style="direction: rtl; background-color: #EBEDF6;">""" + """

    <!-- HEADER -->
    <table class="head-wrap" background-color="#999999">
        <tr>
            <td></td>
            <td class="header container">

                <div class="content" style="background-color: #d3d3d3;">
                    <table background-color="#999999">
                        <tr>
                                <h6 class="collapse">{}</h6>
                            </td>
                        </tr>
                    </table>
                </div>

            </td>
            <td></td>
        </tr>
    </table><!-- /HEADER -->""".format(broker_name) + """


    <!-- BODY -->
    <table class="body-wrap">
        <tr>
            <td></td>
            <td class="container" background-color="#FFFFFF">

                <div class="content" style="background-color: whitesmoke;">
                    <table>
                        <tr>
                            <td>


                                <p class="lead"> با سلام و احترام
                                </p>

                                    <br />
                                <br />

                                        """ + str(content) + """

                                <!-- social & contact -->
                                <br>
                                <br>
                                <p class="callout">
                                     این ایمیل بنا به درخواست شما و بصورت اتوماتیک از طرف {} برای شما
                                    ارسال شده است، لطفا از پاسخ دادن به آن خودداری نمایید.
                                </p>
                            </td>
                        </tr>
                    </table>
                </div>

            </td>
            <td></td>
        </tr>
    </table><!-- /BODY -->

    <!-- FOOTER -->
    <!-- <table class="footer-wrap">
<tr>
<td></td>
<td class="container">

<div class="content">
<table>
<tr>
<td align="center">
<p>
<a href="#">Terms</a> |
<a href="#">Privacy</a> |
<a href="#"><unsubscribe>Unsubscribe</unsubscribe></a>
</p>
</td>
</tr>
</table>
</div>

</td>
<td></td>
</tr>
</table>
-->
</body>

</html>""".format(broker_name)


def check_otp(type, data, db):
    otp_cache = db.cache("otp")
    check_result = {"check": False}
    cache_data = otp_cache.get(data.get(type))
    if str(cache_data) in ["", "None", "null"]:
        return check_result
    correct = json.loads(str(cache_data))
    if int(correct["correct"]) == int(data["otp"]):
        check_result["check"] = True
    return check_result


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
    result = requests.post(url="https://api.zarinpal.com/pg/v4/payment/request.json",
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


class IncorrectLoginData(UserInputError):
    def __init__(self, msg):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(IncorrectLoginData, self).__init__(message=msg, error_code=error_code_base + 101,
                                                 persian_massage='نام کاربری یا رمز عبور اشتباه است.')


class DuplicatedMember(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(DuplicatedMember, self).__init__(message="Member is already exist ",
                                               error_code=error_code_base + 102,
                                               persian_massage="کاربری با این مشخصات وجود دارد.")


class InvalidCurrentPassword(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(InvalidCurrentPassword, self).__init__(message="Current password is invalid",
                                                     error_code=error_code_base + 103,
                                                     persian_massage="پسورد فعلی اشتباه وارد شده است."
                                                     )


class InvalidPasswordStructure(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(InvalidPasswordStructure, self).__init__(message="Password structure is invalid",
                                                       error_code=error_code_base + 104)


class InvalidOtp(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(InvalidOtp, self).__init__(message="invalid otp",
                                         error_code=error_code_base + 106,
                                         persian_massage="کد وارد شده اشتباه وارد شده است."
                                         )


def change_wallet_balance(data, member, mongo):
    if member["_id"] != data["member_id"]:
        raise PermissionError()

    update_result = set_new_wallet_balance(new_balance=data["new_balance"], member_id=member["_id"],
                                     mongo=mongo)
    result = {"id": update_result["_id"], "result": update_result["result"]}
    return result


def set_new_wallet_balance(wallet_balance,payment_cost, member_id, mongo):

    if wallet_balance < payment_cost:
        raise ValueError("Insufficient wallet balance for payment")

    update_body = {
        "wallet_balance": wallet_balance - payment_cost
    }
    myquery = {"_id": member_id}
    newvalues = {"$set": {**update_body}}

    update_result = mongo.update_one(myquery, newvalues)

    update_result = {"_id": member_id, "result": update_result.raw_result}
    return update_result



def check_verification_code(type, data, db):
    verification_code_cache = db.cache("verification_code")
    check_result = {"check": False}
    cache_data = verification_code_cache.get(data.get(type))
    if str(cache_data) in ["", "None", "null"]:
        return check_result
    correct = json.loads(str(cache_data))
    if int(correct["correct"]) == int(data["otp"]):
        check_result["check"] = True
    return check_result

class InvalidVerificationCode(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(InvalidOtp, self).__init__(message="invalid otp",
                                         error_code=error_code_base + 106,
                                         persian_massage="کد وارد شده اشتباه وارد شده است."
                                         )
class PaymentFailed(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(PaymentFailed, self).__init__(message="Payment Failed ",
                                            error_code=error_code_base + 107,
                                            persian_massage="پرداخت ناموفق بود .")


class PaymentException(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["members"])
        super(PaymentException, self).__init__(message="Payment exception ",
                                               error_code=error_code_base + 108,
                                               persian_massage="پرداخت ناموفق بود .")


class DuplicatedCharge(UserInputError):
    def __init__(self):
        cfg_helper = ConfigHelper()
        error_code_base = int(cfg_helper.get_config("CUSTOM_ERROR_CODES")["events"])
        super(DuplicatedCharge, self).__init__(message="wallet is already charge ",
                                               error_code=error_code_base + 109,
                                               persian_massage="قبلا با این تراکنش حساب کاربری شارژ شده است  .")
