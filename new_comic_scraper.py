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
                if m:
                    title, volume = parse_title(m.group(1))
                author = re.sub(r"<a.*>", "", c[1].replace("</p>", "").strip())

                books.append({
                    "title": title,
                    "volume": volume,
                    "author": author,
                    "release_date": release_date
                })
    return books


def parse_title(title):
    pts = ["（([0-9]+)）$", "\(([0-9]+)\)\s*$"]
    parsed_title, volume = title, 1

    for pt in pts:
        m = re.compile(pt).search(title)
        if m:
            volume = int(m.group(1))
            parsed_title = title.replace(m.group(0), "")
            break

    return parsed_title, volume


def post_comic_data(url, comics):
    for comic in comics:
        params = {
            "title": comic["title"],
            "author": comic["author"],
            "volume": comic["volume"],
            "release_date": comic["release_date"]
        }
        requests.post(url, params)


if __name__ == "__main__":

    NATALIE_URL = "http://natalie.mu/comic/feed/news"
    API_URL = "http://localhost:8888/api/newcomics"

    urls = get_urls(NATALIE_URL)
    comics = get_comic_data(urls)
    post_comic_data(API_URL, comics)
