class BencodeError(Exception):
    pass


class BencodeEncodeError(BencodeError):
    pass


class BencodeDecodeError(BencodeError):
    pass
