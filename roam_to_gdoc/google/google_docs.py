from itertools import chain
from typing import List, Dict

from roam_to_gdoc.element import Element
from roam_to_gdoc.parse_markdown import markdown_to_style_and_text
from roam_to_gdoc.roam.block_to_elements import flatten_children


def element_to_updates(element: Element, page_to_id) -> List[Dict]:
    styles, text = markdown_to_style_and_text(element.text.replace("\n", "\v"), page_to_id)
    return [
        {
            "insertText": {
                "text": "\n",
                "location": {
                    "index": 1,
                    "segmentId": None,
                },
            },
        },
        # Need to insert newline before deleting bullets,
        # otherwise will delete previous element's bullet
        {
            "deleteParagraphBullets": {
                "range": make_range(1, 2),
            },
        },
        {
            "insertText": {
                "text": "\t" * max(element.indentation - 1, 0) + text + " ",
                "location": {
                    "index": 1,
                    "segmentId": None,
                },
            },
        },
        *(
            [{
                "createParagraphBullets": {
                    "range": make_range(1, 2),
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                },
            }]
            if element.indentation > 0 else []
        ),
        update_paragraph_style(element.heading, 1, 2),
        *(
            {
                "updateTextStyle": {
                    "textStyle": {
                        style.type: {"url": style.url} if style.type == "link" else True,
                    },
                    "fields": style.type,
                    "range": make_range(1 + style.start, 1 + style.end),
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
    elements = (
        list(reversed(flatten_children(page["children"])))
        if "children" in page else []
    )
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
                    ]
                    if end_index > 1 else []
                ),
                *chain.from_iterable(
                    element_to_updates(element, page_to_id)
                    for element in elements
                ),
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
