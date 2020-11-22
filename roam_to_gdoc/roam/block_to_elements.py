from itertools import chain
from typing import List

from roam_to_gdoc.element import Element


def block_to_elements(block, indentation=0) -> List[Element]:
    element = Element(
        text=block["string"],
        indentation=indentation,
        heading=block.get("heading"),
    )

    if "children" in block:
        return [element] + flatten_children(block["children"], indentation + 1)

    return [element]


def flatten_children(children, indentation=0):
    return list(chain.from_iterable(
        block_to_elements(block, indentation) for block in children
    ))
