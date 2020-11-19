from dataclasses import dataclass
from typing import Optional


@dataclass
class Element:
    text: str
    style: Optional[str] = None
    heading: Optional[int] = None
    indentation: int = 0


@dataclass
class Style:
    start: int
    end: int
    type: str
    url: Optional[str] = None
