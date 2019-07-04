import feedparser
NewsFeed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")

print(NewsFeed.entries[1].keys())

for entry in NewsFeed.entries:
    print("%s|%s|%s" % (entry.link, entry.title, entry.published))
    print('-' * 20)


# if 'title' in NewsFeed.entries[1].keys():
#     html_content = ""
#     for entry in NewsFeed.entries:
#         html_content += '<div class="ti_news">%s</div>\n' % entry.title
#     print(html_content)
#