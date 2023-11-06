from helpers.communication_helpers import create_persian_error_message


class BaseError(Exception):
    def __init__(self, message, error_code, persian_massage):
        super(BaseError, self).__init__(message)
        self.error_code = error_code
        self.persian_massage = persian_massage


def create_exception_response(status, tracking_code, method_type, error, broker_type, source, member_id, error_persian):
    return create_persian_error_message(method=method_type, record={}, broker_type=broker_type, source=source,
                                        tracking_code=tracking_code, error_code=status,
                                        is_successful=False, error_description=error, member_id=member_id,
                                        error_persian_description=error_persian)
