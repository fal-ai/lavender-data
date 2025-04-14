class ReaderException(Exception):
    pass


class ReaderColumnsRequired(ReaderException):
    pass


class ReaderFormatInvalid(ReaderException):
    pass


class ReaderColumnsInvalid(ReaderException):
    pass


class ReaderDirnameOrFilepathRequired(ReaderException):
    pass
