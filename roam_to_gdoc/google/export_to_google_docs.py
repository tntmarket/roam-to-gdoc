import json
from time import sleep
from typing import Dict, Tuple

from googleapiclient.discovery import build
import iso8601

from roam_to_gdoc.google.credentials import get_credentials
from roam_to_gdoc.google.google_docs import rewrite_document

DOCUMENT_TITLE = "Test Page Yolo"

# TODO - [[One]] ... [[Two]], using recursive regex
# TODO - [alias]([[link]])
# TODO - Images
# TODO - De-dent every bullet once, have the top level be plain paragraphs

# TODO - Attr::
# TODO - Backlinks
# TODO - {{table}}

pages = [
    {
        "title": "P: Yolo Dolo",
        "children": [
            {
                "string": "YOLO **SWAG** BRO",
            },
            {
                "string": "My **__crayfish__** is [[Trolo Molo]]",
                "heading": 1,
            },
            {
                "string": "[Yes](https://www.google.com) it is",
                "children": [
                    {
                        "string": "Line...\nBreak?",
                    },
                    {
                        "string": "Baaaa [humbug]([[Hamburger]])",
                    },
                ]
            },
        ]
    },
    {
        "title": "Trolo Molo",
        "children": [
            {
                "string": "a [[P: Yolo Dolo]] b",
                "children": [
                    {
                        "string": "No!!",
                    },
                    {
                        "string": "Yes!?",
                    },
                ]
            },
            {
                "string": "This goes back to [[Yolo Dolo]] too",
            },
            {
                "string": "Yeah that's right",
            },
        ]
    },
]


def main():
    docs = build('docs', 'v1', credentials=get_credentials())
    drive = build('drive', 'v3', credentials=get_credentials())

    with open('tmp/davelu-yelp.json') as f:
        pages = json.load(f)

        folder_id = upsert_folder(drive)

        def title_to_id(title):
            return upsert_document(drive, docs, title, folder_id)[0]['documentId']

        for page in pages:
            document, just_created = upsert_document(drive, docs, page["title"], folder_id)
            if just_created or page["edit-time"] / 1000 > last_modified(drive, document["documentId"]):
                print('Rewriting {}'.format(page['title']))
                rewrite_document(docs, document, page, title_to_id)
                # Throttle, to avoid usage limit https://developers.google.com/docs/api/limits
                sleep(1)


document_by_title = {}
just_created_by_title = {}


def upsert_document(drive, docs, title, folder_id) -> Tuple[Dict, bool]:
    if title in document_by_title:
        return document_by_title[title], just_created_by_title[title]

    matches = drive.files().list(corpora="user", q="name = '{}'".format(title.replace("'", "\\'"))).execute()['files']
    if matches:
        document_id = matches[0]['id']
        print("'{}' already exists".format(title))
        document = get_document(docs, document_id)
        document_by_title[title] = document
        just_created_by_title[title] = False
        return document, False

    print("Creating '{}'".format(title))
    document = docs.documents().create(body={"title": title}).execute()
    document_by_title[title] = document
    just_created_by_title[title] = True
    drive.files().update(fileId=document['documentId'], addParents=folder_id).execute()
    return document, True


def last_modified(drive, document_id: str) -> int:
    time_string = drive.files().get(fileId=document_id, fields="modifiedTime").execute()["modifiedTime"]
    return iso8601.parse_date(time_string).timestamp()


FOLDER_NAME = "Roam Export"


def upsert_folder(drive):
    matches = drive.files().list(corpora="user", q="name = '{}'".format(FOLDER_NAME)).execute()['files']
    if matches:
        assert matches[0]['mimeType'] == 'application/vnd.google-apps.folder'
        return matches[0]['id']

    print("Creating {} Folder".format(FOLDER_NAME))
    folder = drive.files().create(
        body={
            'name': FOLDER_NAME,
            'mimeType': 'application/vnd.google-apps.folder'
        },
        fields="id"
    ).execute()
    return folder['id']


def get_document(docs, document_id):
    return docs.documents().get(documentId=document_id).execute()


if __name__ == '__main__':
    main()
