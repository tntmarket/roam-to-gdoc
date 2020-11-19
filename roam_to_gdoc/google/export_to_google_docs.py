from googleapiclient.discovery import build

from roam_to_gdoc.google.credentials import get_credentials
from roam_to_gdoc.google.google_docs import rewrite_document

DOCUMENT_TITLE = "Test Page Yolo"

# TODO - get actually reading json to work

# TODO - [alias]([[link]])
# TODO - [[a [[nested]] link]]
# TODO - Attr::
# TODO - Images
# TODO - Backlinks
# TODO - {{table}}

pages = [
    {
        "title": "Yolo Dolo",
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
                "string": "Yes it is good",
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

    # with open('tmp/davelu-yelp.json') as f:
    #     print(json.load(f))

    page_name_to_document = {}

    folder_id = upsert_folder(drive)
    for page in pages:
        page_name_to_document[page["title"]] = upsert_document(drive, docs, page["title"], folder_id)

    def page_to_id(title):
        return page_name_to_document[title]['documentId']

    for page in pages:
        document = page_name_to_document[page["title"]]
        rewrite_document(docs, document, page, page_to_id)


def upsert_document(drive, docs, title, folder_id):
    matches = drive.files().list(corpora="user", q="name = '{}'".format(title)).execute()['files']
    if matches:
        document_id = matches[0]['id']
        return get_document(docs, document_id)

    print("Creating '{}'".format(title))
    document = docs.documents().create(body={"title": title}).execute()
    drive.files().update(fileId=document['documentId'], addParents=folder_id).execute()
    return document


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
