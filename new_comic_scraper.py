#!/usr/bin/env python
# -*- coding: utf-8 -*-

import feedparser
import requests
import lxml.html
import re
import datetime


def get_urls(url):
    rss = feedparser.parse(url)
    pt = r".*本日発売の単行本リスト"
    entries = [e for e in rss.entries if re.match(pt, e.title.encode("utf-8"))]
    return [e.link for e in entries]


def parse_date(root):
    na_date = root.xpath("//p[@class='NA_date']")[0]
    datelist = na_date.xpath("descendant::time")

    pt = re.compile("(.+日).*")
    m = pt.search(datelist[0].text.encode("utf-8"))

    if m:
        tdatetime = datetime.datetime.strptime(m.group(1), "%Y年%m月%d日")
        tdate = datetime.date(tdatetime.year, tdatetime.month, tdatetime.day)

    return tdate


def get_comic_data(urls):
    books = []

    for url in urls:
        html = requests.get(url).text
        root = lxml.html.fromstring(html)

        release_date = parse_date(root)

        na_article_body = root.xpath("//div[@class='NA_articleBody']")[0]
        elements = na_article_body.xpath("descendant::p")
        elements.pop(0)

        for element in elements:
            comics = lxml.html.tostring(
                element,
                method="html",
                encoding="utf-8",
                pretty_print="True"
            ).split("<br>")

            for comic in comics:
                c = comic.split("</a>")
                m = re.compile("「(.+)」$").search(c[0])
                if m: title = m.group(1)
                author = re.sub(r"<a.*>", "", c[1].replace("</p>", "").strip())

                books.append({
                    "title": title,
                    "author": author,
                    "release_date": release_date
                })
    return books


if __name__ == "__main__":

    NATALIE_URL = "http://natalie.mu/comic/feed/news"

    urls = get_urls(NATALIE_URL)
    comics = get_comic_data(urls)
