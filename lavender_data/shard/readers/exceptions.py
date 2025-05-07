class ReaderException(Exception):
    pass


class ReaderFormatInvalid(ReaderException):
    pass


class ReaderColumnsInvalid(ReaderException):
    pass


class ReaderDirnameOrFilepathRequired(ReaderException):
    pass


class ReaderPrepareFailed(ReaderException):
    pass
