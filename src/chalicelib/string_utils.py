from typing import Union, Tuple

def ellipsis(old: Union[str, None], new: str) -> str:
    if old:
        return f'{old[:-3]}{new} ...'
    else:
        return f'{new} ...'

def split(old: Union[str, None], new: str) -> Tuple[str, Union[str, None]]:
    length = 4096 - 4
    if old:
        length -= len(old) - 3

    if len(new) < length:
        return (ellipsis(old, new), None)

    index = new[:length].rfind(' ')
    return (ellipsis(old, new[:index]), new[index + 1:])
