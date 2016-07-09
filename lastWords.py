
import json
import threading
#import urllib2

from multiprocessing import Pool
from urllib.request import urlopen

import ssl
import http.client

import codecs

"""
Global variables
"""

_DECODER = codecs.getreader("utf-8")
# To prevent SSL failure after too many calls.
_CONTEXT = ssl._create_unverified_context()
_LOCK = threading.Lock()

modData = json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/user/dang.json", context=_CONTEXT)))
submitIds = modData["submitted"]

# Uncomment for test data
submitIds = [10551997, 7867166, 12041458, 12059888]
DEBUG = True

def isComment(data):
  return data is not None \
    and "type" in data \
    and data["type"] == "comment" \
    and "text" in data

def isPossibleBan(data):
  return isComment(data) \
    and "banned" in data["text"] \
    and "parent" in data

def isUserBanned(parentComment, modComment):
  return True

def processItem(id):
  if DEBUG:
    print(id)

  modComment = ""
  try:
    modComment = json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/item/"
      + str(id)
      + ".json",
      context=_CONTEXT)))
  except http.client.BadStatusLine:
    print("***********************************************")
    print("failed: " + str(id))
    print("***********************************************")
    return 0

  if isPossibleBan(modComment):
    parentComment = json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/item/"
      + str(modComment["parent"])
      + ".json",
      context=_CONTEXT)))

    if isUserBanned(parentComment, modComment):
      _LOCK.acquire()
      with open("README.md", 'a') as out:
        out.write(parentComment["text"] + '\n\n')
      _LOCK.release()
    return 1
  return 0

def run_job():
  pool = Pool(8)
  results = pool.map(processItem, submitIds)

  pool.close()
  pool.join()

  print("Finished")
  print("Total banned users detected: " + str(sum(results)))

