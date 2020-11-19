from itertools import chain
from typing import List, Dict

from roam_to_gdoc.element import Element
from roam_to_gdoc.parse_markdown import markdown_to_style_and_text
from roam_to_gdoc.roam import flatten_children


def element_to_updates(element: Element, page_to_id) -> List[Dict]:
    styles, text = markdown_to_style_and_text(element.text.replace("\n", "\v"), page_to_id)
    start = element.indentation + 1
    return [
        {
            "insertText": {
                "text": "\t" * element.indentation + text + "\n",
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


def rewrite_document(docs, document, page, page_to_id):
    end_index = get_end_index(document)
    elements = list(reversed(flatten_children(page["children"])))
    body_length = len('\n'.join(markdown_to_style_and_text(element.text, page_to_id)[1] for element in elements))
    docs.documents().batchUpdate(
        documentId=document['documentId'],
        body={
            # Fill in the document backwards, so we can keep 0 index offset
            "requests": [
                *(
                    [
                        {
                            "deleteContentRange": {
                                "range": make_range(1, end_index),
                            },
                        },
                        {
                            "deleteParagraphBullets": {
                                "range": make_range(1, 2),
                            },
                        },
                    ]
                    if end_index > 1 else []
                ),
                *chain.from_iterable(
                    element_to_updates(element, page_to_id)
                    for element in elements
                ),
                # Bullet-ify after, to get convert indents into levels
                {
                    "createParagraphBullets": {
                        "range": make_range(1, body_length + 1),
                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                    },
                },
                {
                    "insertText": {
                        "text": "\n",
                        "location": {
                            "index": 1,
                            "segmentId": None,
                        },
                    },
                },
                {
                    "deleteParagraphBullets": {
                        "range": make_range(1, 2),
                    },
                },
                element_to_updates(Element(text=page["title"], heading=0), page_to_id),
            ],
        },
    ).execute()


def get_end_index(document):
    elements = document['body']['content']
    # Exclude newline at end of segment
    return elements[-1]['endIndex'] - 1
