import feedparser
NewsFeed = feedparser.parse("http://feeds.bbci.co.uk/news/rss.xml")

if 'title' in NewsFeed.entries[1].keys():
    html_content = ""
    for entry in NewsFeed.entries:
        html_content += '<div class="ti_news">%s</div>\n' % entry.title
    print(html_content)