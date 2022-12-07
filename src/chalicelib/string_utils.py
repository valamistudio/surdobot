from __future__ import annotations
from typing import Tuple

def __concat(old: str | None, new: str, ellipsis: bool) -> str:
    return f'{old[:-3] if old else ""}{new}{" ..." if ellipsis else ""}'

def split(old: str | None, new: str) -> Tuple[str, str | None]:
    length = 4096 - 4
    if old:
        length -= len(old) - 3

    if len(new) < length:
        return (__concat(old, new, True), None)

    index = new[:length].rfind(' ')
    return (__concat(old, new[:index], False), __concat(None, new[index + 1:], True))
