from itertools import chain
from typing import List, Dict

from element import Element


def element_to_insert_request(element: Element) -> List[Dict]:
    text = (
        "\t" * element.indentation +
        element.text.replace("\n", "\v") +
        "\n" * (2 if element.extra_line else 1)
    )
    return [
        {
            "insertText": {
                "text": text,
                "location": {
                    "index": 1,
                    "segmentId": None,
                },
            },
        },
        *(
            [update_paragraph_style(element.heading, 1, 2)]
            if element.heading else []
        ),
        update_style(1, len(text) + 1, bold=element.bold, italic=element.italic, url=element.url),
    ]


def make_range(start, end):
    return {
        "segmentId": None,
        "startIndex": start,
        "endIndex": end,
    }


def update_paragraph_style(style, start, end):
    return {
        "updateParagraphStyle": {
            "paragraphStyle": {
                "namedStyleType": style,
            },
            "fields": "namedStyleType",
            "range": make_range(start, end),
        },
    }


def update_style(
    start,
    end,
    bold=False,
    italic=False,
    url=None,
):
    return {
        "updateTextStyle": {
            "textStyle": {
                "bold": bold,
                "italic": italic,
                "link": {"url": url} if url else None,
            },
            "fields": "bold,italic,link",
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