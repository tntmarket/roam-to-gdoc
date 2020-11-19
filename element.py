from dataclasses import dataclass
from typing import Optional


@dataclass
class Element:
    text: str
    style: Optional[str] = None
    heading: Optional[str] = None
    indentation: int = 0
    extra_line: bool = False
    bold: bool = False
    italic: bool = False
    url: Optional[str] = None


