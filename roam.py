from itertools import chain
from typing import List

from element import Element


def block_to_elements(json, indentation=0) -> List[Element]:
    element = Element(
        text=json["string"],
        indentation=indentation,
        heading=json.get("heading"),
    )

    if "children" in json:
        return [element] + flatten_children(json["children"], indentation + 1)

    return [element]


def flatten_children(children, indentation=0):
    return list(chain.from_iterable(
        block_to_elements(block, indentation) for block in children
    ))
