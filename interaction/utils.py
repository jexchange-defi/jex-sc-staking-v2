
import codecs


def ensure_even_length(string: str) -> str:
    if len(string) % 2 == 1:
        return '0' + string
    return string


def hex2dec(hex_):
    return int(hex_, 16)


def str2hex(str_):
    return codecs.encode(bytes(str_, 'ascii'), 'hex').decode("ascii")
