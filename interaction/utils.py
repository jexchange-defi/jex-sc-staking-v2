
def ensure_even_length(string: str) -> str:
    if len(string) % 2 == 1:
        return '0' + string
    return string
