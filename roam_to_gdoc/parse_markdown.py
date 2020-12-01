import re
import xml.etree.ElementTree as etree

import markdown
from markdown.extensions.wikilinks import WikiLinkExtension
from html.parser import HTMLParser

from markdown.inlinepatterns import InlineProcessor
from regex import regex

from roam_to_gdoc.element import Style


class RoamDoubleBracketExtension(WikiLinkExtension):

    def extendMarkdown(self, md):
        self.md = md
        WIKILINK_RE = r'(\[\[([^\[\]]|(?1))*\]\])(?1)*'
        wikilinkPattern = RoamDoubleBracketInlineProcessor(WIKILINK_RE, self.getConfigs())
        wikilinkPattern.md = md
        md.inlinePatterns.register(wikilinkPattern, 'wikilink', 75)


class RoamDoubleBracketInlineProcessor(InlineProcessor):
    def __init__(self, pattern, config):
        self.pattern = pattern
        self.config = config
        self.compiled_re = regex.compile(pattern, re.DOTALL | re.UNICODE)

    def handleMatch(self, m, data):
        if m.group(1).strip():
            label = m.group(1).strip()[2:-2]
            url = self.config['build_url'](label)
            a = etree.Element('a')
            a.text = label
            a.set('href', url)
        else:
            a = ''
        return a, m.start(0), m.end(0)


def markdown_to_style_and_text(text, page_to_id):
    def page_name_to_url(label):
        return 'https://docs.google.com/document/d/{}'.format(page_to_id(label))

    html = markdown.markdown(re.sub(r'__', r'_', text), extensions=[
        RoamDoubleBracketExtension(build_url=page_name_to_url, html_class=None)
    ])
    parser = StyleParser()
    parser.feed(html)
    return parser.styles, parser.text, parser.images


class StyleParser(HTMLParser):
    def __init__(self):
        super(StyleParser, self).__init__()
        self.text = ''
        self.bolds = []
        self.italics = []
        self.links = []
        self.styles = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        if tag == 'strong':
            self.bolds.append(self.i())
        elif tag == 'em':
            self.italics.append(self.i())
        elif tag == 'a':
            self.links.append((self.i(), attrs[0][1]))
        elif tag == 'img':
            self.images.append((self.i(), attrs[1][1]))

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


if __name__ == '__main__':
    print(
        markdown_to_style_and_text(
            "[[123]] abc",
            {
                '123': '123',
            }.get,
        )
    )
    print(
        markdown_to_style_and_text(
            "__hello__ my **dudes** \v how [[P: are]] you __doing__? [[hello [[yeah]] blah]]",
            {
                'P: are': 'YEEEEEEE',
                'hello [[yeah]] blah': 'heyblah',
            }.get,
        )
    )
    print(
        markdown_to_style_and_text(
            "Measuring [[Coding Outcome]]s is challenging because [[Coding decisions play out over the time scale of months or years]],",
            {
                'P: are': 'YEEEEEEE',
                'hello [[yeah]] blah': 'heyblah',
            }.get,
        )
    )
    print(
        markdown_to_style_and_text(
            "![](https://www.google.com) thing",
            {}.get,
        )
    )
