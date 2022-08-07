import string

__all__ = [
    'b64alphabet',
    'int_to_b64',
    'b64_to_int',
]


b64alphabet = string.ascii_uppercase + string.ascii_lowercase + string.digits + '-_'


def int_to_b64(n):
    n, r = divmod(n, 64)
    c = b64alphabet[r]
    if n == 0:
        return c
    else:
        return int_to_b64(n) + c


def b64_to_int(b64):
    r = b64alphabet.index(b64[-1])
    if len(b64) == 1:
        return r
    else:
        return r + b64_to_int(b64[:-1]) * 64


def b64encode(x):
    if hasattr(x, '__base64__'):
        return x.__base64__()
    elif hasattr(x, '__int__'):
        return int_to_b64(int(x))
    elif isinstance(x, int):
        return int_to_b64(x)
    else:
        raise ValueError("Cannot convert {} of type {} to base64".format(x, type(x)))
