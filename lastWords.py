
import json
import threading
import urllib2

from multiprocessing import Pool

import ssl
import httplib

# This restores the same behavior as before.
context = ssl._create_unverified_context()

lock = threading.Lock()



modFile = open("modComments.txt", "w")

modData = json.load(urllib2.urlopen("https://hacker-news.firebaseio.com/v0/user/dang.json", context=context))
#submitIds = [10289260]
submitIds = modData["submitted"]

print(len(submitIds))

for id in submitIds:
	if type(id) != type(3):
		print(type(id))

def isBanningComment(data):
	return "type" in data \
		and data["type"] == "comment" \
		and "text" in data \
		and "banned" in data["text"] \
		and "parent" in data

def foo(id):
	modComment = ""
	try:
		modComment = json.load(urllib2.urlopen("https://hacker-news.firebaseio.com/v0/item/"
			+ str(id)
			+ ".json",
			context=context))
	except httplib.BadStatusLine:
		print("failed: " + str(id))
		raise 10
		return 0

	if isBanningComment(modComment):

		lock.acquire()
		#next check if user is banned
		print("id: " + str(modComment['id']))

		modCommentText = modComment["text"]
		modCommentText = modCommentText.encode('utf-8')

		print("banned text: " + modCommentText)
		modFile.write(modCommentText)
		modFile.write("\n\n")
		lock.release()
		return 1
	else:
		return 0

pool = Pool(16) 
results = pool.map(foo, submitIds)

pool.close()
pool.join()

modFile.close()
print("Finished")
print(sum(results))

