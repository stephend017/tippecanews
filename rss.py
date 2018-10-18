import feedparser
import sqlite3
import requests


conn = sqlite3.connect("test.db")
c = conn.cursor()

xml_links = ["http://www.purdue.edu/newsroom/rss/academics.xml", "http://www.purdue.edu/newsroom/rss/AdvNews.xml", "http://www.purdue.edu/newsroom/rss/AgriNews.xml"]

for link in xml_links:
	d = feedparser.parse(link)
	try:
		for x in d.entries:
			print str(x.title)
			print str(x.link)
			print str(x.published)
			print str(x.summary)
			print "\n"

			c.execute("select * from purdue_news where title=?", (x.title,))

			if(not c.fetchone()):
				payload = {'text':x.title}
				requests.post("https://hooks.slack.com/services/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", json=payload)

			c.execute("insert or ignore into purdue_news(title, link, published, summary) values(? ,? ,? ,?)", (x.title, x.link, x.published, x.summary))
		pass
	except:
		pass


conn.commit()



conn.close()