import json
import urllib2


def isBanningComment(data):
	return "type" in data \
		and data["type"] == "comment" \
		and "text" in data \
		and "banned" in data["text"]

modData = json.load(urllib2.urlopen("https://hacker-news.firebaseio.com/v0/user/dang.json"))
submitIds = modData["submitted"]#[12051346, 12041273, 12041271, 12041257, 12031191, 12028698, 12023963]

for id in submitIds:
	modComment = json.load(urllib2.urlopen("https://hacker-news.firebaseio.com/v0/item/"
		+ str(id)
		+ ".json"))
	if isBanningComment(modComment):
		#next check if user is banned
		print(modComment["text"])
