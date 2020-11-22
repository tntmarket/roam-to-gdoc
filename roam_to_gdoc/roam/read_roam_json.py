import json
import re
from pprint import pprint


def get_pages():
    with open('tmp/davelu-yelp.json') as f:
        return inline_block_refs_completely(json.load(f))


def map_all_blocks(pages, block_to_string_fn):
    def map_blocks(blocks):
        return [
            {
                **block,
                "string": block_to_string_fn(block),
                **transform_children(block),
            }
            for block in blocks
        ]

    def transform_children(block):
        return (
            {
                "children": map_blocks(block["children"]),
            }
            if "children" in block else {}
        )

    return [
        {
            **page,
            **transform_children(page),
        }
        for page in pages
    ]


BLOCK_REF_PATTERN = re.compile('\(\(.{9}\)\)')


def inline_block_refs_once(pages):
    block_refs_found = False
    uid_to_string = {}

    def associate_uids(block):
        if "uid" in block:
            uid_to_string[block["uid"]] = block["string"]

    map_all_blocks(pages, associate_uids)

    def inline_refs_in_block(block):
        nonlocal block_refs_found
        string = block["string"]
        for match in BLOCK_REF_PATTERN.finditer(string):
            start, end = match.regs[0]
            block_ref = match.string[start:end]
            string = string.replace(block_ref, uid_to_string[block_ref[2:-2]])
            block_refs_found = True

        return string

    return map_all_blocks(pages, inline_refs_in_block), block_refs_found


def inline_block_refs_completely(pages):
    block_refs_found = True
    while block_refs_found:
        pages, block_refs_found = inline_block_refs_once(pages)

    return pages


if __name__ == '__main__':
    pprint(
        inline_block_refs_completely([
            {
                "title": "Page 1",
                "children": [
                    {
                        "string": "block 1",
                        "children": [
                            {
                                "string": "1 a",
                                "children": [
                                    {
                                        "string": "block 1 a x - ((D4kiNIPj1)) yo",
                                        "uid": "crp8u5oJf"
                                    },
                                    {
                                        "string": "block 1 a y",
                                        "uid": "D4kiNIPj1"
                                    },
                                ]
                            },
                        ]
                    },
                    {
                        "string": "block 2",
                        "heading": 1,
                    },
                    {
                        "string": "block 3",
                        "children": [
                            {
                                "string": "block 3 a",
                            },
                            {
                                "string": "block 3 b",
                            },
                        ]
                    },
                ]
            },
            {
                "title": "Page 2",
                "children": [
                    {
                        "string": "block 1",
                        "children": [
                            {
                                "string": "block 1 a, ((crp8u5oJf))",
                            },
                            {
                                "string": "block 1 b",
                            },
                        ]
                    },
                    {
                        "string": "block 2",
                    },
                    {
                        "string": "block 3",
                    },
                ]
            },
        ])
    )
