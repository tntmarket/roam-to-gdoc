import re
import markdown
from markdown.extensions.wikilinks import WikiLinkExtension
from html.parser import HTMLParser

from element import Style


def markdown_to_style_and_text(text):
    html = markdown.markdown(re.sub(r'__', r'_', text), extensions=[
        WikiLinkExtension(build_url=page_name_to_url, html_class=None)
    ])
    parser = StyleParser()
    parser.feed(html)
    return parser.styles, parser.text


class StyleParser(HTMLParser):
    def __init__(self):
        super(StyleParser, self).__init__()
        self.text = ''
        self.bolds = []
        self.italics = []
        self.links = []
        self.styles = []

    def handle_starttag(self, tag, attrs):
        if tag == 'strong':
            self.bolds.append(self.i())
        elif tag == 'em':
            self.italics.append(self.i())
        elif tag == 'a':
            self.links.append((self.i(), attrs[0][1]))

    def handle_endtag(self, tag):
        if tag == 'strong':
            self.styles.append(
                Style(
                    type='bold',
                    start=self.bolds.pop(),
                    end=self.i(),
                )
            )
        elif tag == 'em':
            self.styles.append(
                Style(
                    type='italic',
                    start=self.italics.pop(),
                    end=self.i(),
                )
            )
        elif tag == 'a':
            (start, url) = self.links.pop()
            self.styles.append(
                Style(
                    type='link',
                    start=start,
                    end=self.i(),
                    url=url,
                )
            )

    def handle_data(self, data):
        self.text += data

    def i(self):
        return len(self.text)


def page_name_to_url(label, base, end):
    return 'https://docs.google.com/document/d/{}'.format(label)


if __name__ == '__main__':
    print(markdown_to_style_and_text("\t\t\t __hello__ my **dudes** \v how [[are]] you __doing__?"))
