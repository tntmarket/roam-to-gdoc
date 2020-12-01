from itertools import chain
from typing import List, TypeVar, Callable, Dict

from roam_to_gdoc.element import Element


def block_to_elements(block, indentation=0) -> List[Element]:
    element = Element(
        text=block["string"],
        indentation=indentation,
        heading=block.get("heading"),
    )

    if "children" in block:
        return [element] + flatten_children(block["children"], indentation + 1, block_to_elements)

    return [element]


T = TypeVar('T')


def flatten_children(
    children,
    indentation=0,
    map_fn: Callable[[Dict, int], List[T]] = block_to_elements,
) -> List[T]:
    return list(chain.from_iterable(
        map_fn(block, indentation) for block in children
    ))


def block_to_edit_times(block, indentation) -> List[int]:
    if "children" in block:
        return [block["edit-time"]] + flatten_children(block["children"], map_fn=block_to_edit_times)

    return [block["edit-time"]]
