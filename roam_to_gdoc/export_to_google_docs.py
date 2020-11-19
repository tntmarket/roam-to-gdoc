from typing import List, TypeVar

from googleapiclient.discovery import build

from roam_to_gdoc.credentials import get_credentials, API_KEY
from roam_to_gdoc.element import Element
from roam_to_gdoc.roam import flatten_children
from roam_to_gdoc.google_docs import make_range, rewrite_document, get_end_index

DOCUMENT_TITLE = "Test Page Yolo"

# TODO - get actually reading json to work

# TODO - [alias]([[link]])
# TODO - Attr::
# TODO - Images
# TODO - Backlinks
# TODO - {{table}}

T = TypeVar('T')


def filter_none(xs: List[T]) -> List[T]:
    return [x for x in xs if x]


def main():
    docs = build('docs', 'v1', credentials=get_credentials(), developerKey=API_KEY)
    drive = build('drive', 'v3', credentials=get_credentials(), developerKey=API_KEY)

    document = upsert_document(drive, docs, DOCUMENT_TITLE)
    page = {
        "title": DOCUMENT_TITLE,
        "children": [
            {
                "string": "YOLO **SWAG** BRO",
            },
            {
                "string": "My **__crayfish__** is [[demanding]]",
                "heading": 1,
            },
            {
                "string": "[Yes](https://www.google.com) it is",
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

    rewrite_document(docs, document, [
        Element(text=page["title"], heading=0, extra_line=True),
        *flatten_children(page["children"]),
    ])

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


if __name__ == '__main__':
    main()
