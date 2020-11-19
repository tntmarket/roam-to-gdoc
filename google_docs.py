from itertools import chain
from typing import List, Dict

from element import Element
from parse_markdown import markdown_to_style_and_text


def element_to_insert_request(element: Element) -> List[Dict]:
    styles, text = markdown_to_style_and_text(element.text.replace("\n", "\v"))
    start = element.indentation + 1
    return [
        {
            "insertText": {
                "text": "\t" * element.indentation + text + "\n" * (2 if element.extra_line else 1),
                "location": {
                    "index": 1,
                    "segmentId": None,
                },
            },
        },
        update_paragraph_style(element.heading, start, start + 1),
        *(
            {
                "updateTextStyle": {
                    "textStyle": {
                        style.type: {"url": style.url} if style.type == "link" else True,
                    },
                    "fields": style.type,
                    "range": make_range(start + style.start, start + style.end),
                },
            } for style in styles
        ),
    ]


def make_range(start, end):
    return {
        "segmentId": None,
        "startIndex": start,
        "endIndex": end,
    }


NAMED_STYLES = ['TITLE', 'HEADING_1', 'HEADING_2', 'HEADING_3']


def update_paragraph_style(style, start, end):
    return {
        "updateParagraphStyle": {
            "paragraphStyle": {
                "namedStyleType": 'NORMAL_TEXT' if style is None else NAMED_STYLES[style],
            },
            "fields": "namedStyleType",
            "range": make_range(start, end),
        },
    }


def rewrite_document(docs, document, elements):
    end_index = get_end_index(document)
    docs.documents().batchUpdate(
        documentId=document['documentId'],
        body={
            "requests": [
                *(
                    [
                        {
                            "deleteContentRange": {
                                "range": make_range(1, end_index),
                            },
                        },
                    ]
                    if end_index > 1 else []
                ),
                {
                    "updateParagraphStyle": {
                        "paragraphStyle": {
                            "namedStyleType": "NORMAL_TEXT",
                        },
                        "fields": "namedStyleType",
                        "range": make_range(1, 2),
                    },
                },
                *chain.from_iterable(element_to_insert_request(element) for element in reversed(elements)),
            ],
        },
    ).execute()


def get_end_index(document):
    elements = document['body']['content']
    # Exclude newline at end of segment
    return elements[-1]['endIndex'] - 1