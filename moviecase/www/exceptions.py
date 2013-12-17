
class MovieDbError(Exception):
    status_code = 500

    def __init__(self, message, status_code=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class DbConnectionError(MovieDbError):
    status_code = 500


class DbError(MovieDbError):
    status_code = 500


class ApiDbConnectionError(MovieDbError):
    status_code = 500


class ApiNotFound(MovieDbError):
    status_code = 404


class ApiBadRequest(MovieDbError):
    status_code = 400