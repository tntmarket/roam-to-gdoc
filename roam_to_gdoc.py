from itertools import chain
from typing import List, TypeVar

from googleapiclient.discovery import build

from credentials import get_credentials, API_KEY

DOCUMENT_TITLE = "Test Page Yolo"

# TODO - get actually reading json to work

# Parsing and styling within Paragraphs.
# - Process paragraphs backwards
# - Calculate the offset of styles after replacement
# - Replace the whole paragraph
# - Apply the styles
# TODO - [[links]]
# TODO - **bold**, __italic__
# TODO - [links](url)
# TODO - Heading levels

# TODO - Attr::
# TODO - Images
# TODO - Backlinks
# TODO - {{table}}

T = TypeVar('T')


def filter_none(xs: List[T]) -> List[T]:
    return [x for x in xs if x]


def make_range(start, end):
    return {
        "segmentId": None,
        "startIndex": start,
        "endIndex": end,
    }


def insert_block(
    text,
    indentation=0,
    heading=0,
    extra_line=False,
):
    return [
        {
            "insertText": {
                "text": (
                    "\t" * indentation +
                    ("H{}.".format(heading) if heading else "") +
                    text.replace("\n", "\v") +
                    "\n" * (2 if extra_line else 1)
                ),
                "endOfSegmentLocation": {
                    "segmentId": None,
                },
            },
        },
    ]


def insert_title(title):
    return [
        insert_block(title),
        update_style("TITLE", 1, 3),
    ]


def update_style(style, start, end):
    return {
        "updateParagraphStyle": {
            "paragraphStyle": {
                "namedStyleType": style,
            },
            "fields": "namedStyleType",
            "range": make_range(start, end),
        },
    }


def block_to_inserts(json, indentation=0):
    inserts = insert_block(json["string"], indentation, heading=json.get("heading"))

    if "children" in json:
        return inserts + flatten_children(json["children"], indentation + 1)

    return inserts


def flatten_children(children, indentation=0):
    return list(chain.from_iterable(
        block_to_inserts(block, indentation) for block in children
    ))


def main():
    docs = build('docs', 'v1', credentials=get_credentials(), developerKey=API_KEY)
    drive = build('drive', 'v3', credentials=get_credentials(), developerKey=API_KEY)

    document = upsert_document(drive, docs, DOCUMENT_TITLE)
    end_index = get_end_index(document)
    page = {
        "title": DOCUMENT_TITLE,
        "children": [
            {
                "string": "YOLO SWAG BRO",
            },
            {
                "string": "My crayfish is demanding",
            },
            {
                "string": "Yes it is",
                "children": [
                    {
                        "string": "Line...\nBreak?",
                    },
                    {
                        "string": "B",
                    },
                ]
            },
        ]
    }
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
                *insert_title(page["title"]),
                flatten_children(page["children"]),
            ],
        },
    ).execute()

    document = get_document(docs, document['documentId'])
    end_index = get_end_index(document)
    docs.documents().batchUpdate(
        documentId=document['documentId'],
        body={
            "requests": [
                {
                    "createParagraphBullets": {
                        "range": make_range(len(DOCUMENT_TITLE) + 3, end_index),
                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                    },
                }
            ],
        },
    ).execute()


def upsert_document(drive, docs, title):
    matches = drive.files().list(corpora="user", q="name = '{}'".format(title)).execute()['files']
    if matches:
        document_id = matches[0]['id']
        return get_document(docs, document_id)

    print("Creating '{}'".format(title))
    return docs.documents().create(body={"title": title}).execute()


def get_document(docs, document_id):
    return docs.documents().get(documentId=document_id).execute()


def get_end_index(document):
    elements = document['body']['content']
    # Exclude newline at end of segment
    return elements[-1]['endIndex'] - 1


if __name__ == '__main__':
    main()
