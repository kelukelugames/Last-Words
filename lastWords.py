
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
_LAST_SUBMITTED_THRESHOLD_SECONDS = 1000

DEBUG = True

def __is_comment(data):
  return data is not None \
    and "type" in data \
    and data["type"] == "comment" \
    and "by" in data \
    and "text" in data \
    and "time" in data

def __is_possible_ban(data):
  return __is_comment(data) \
    and "banned" in data["text"] \
    and "parent" in data

def __isUserBanned(user_comment, mod_comment):
  if __is_comment(user_comment) is False:
    return False
  return user_comment["time"] - mod_comment["time"] < _LAST_SUBMITTED_THRESHOLD_SECONDS

def __process_item(id):
  if DEBUG:
    print(id)

  mod_comment = ""
  try:
    mod_comment = json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/item/"
      + str(id)
      + ".json",
      context=_CONTEXT)))
  except http.client.BadStatusLine:
    print("***********************************************")
    print("failed: " + str(id))
    print("***********************************************")
    return 0

  if __is_possible_ban(mod_comment):
    parentComment = json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/item/"
      + str(mod_comment["parent"])
      + ".json",
      context=_CONTEXT)))

    if __isUserBanned(parentComment, mod_comment):
      _LOCK.acquire()
      with open("README.md", 'a') as out:
        out.write(parentComment["text"] + "\n")
        out.write("  --" + parentComment["by"] + "\n\n")
      _LOCK.release()
    return 1
  return 0

def run_job():
  mod_data = json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/user/dang.json", context=_CONTEXT)))
  submit_ids = mod_data["submitted"]

  # Uncomment for test data
  submit_ids = [10551997, 7867166, 12041458, 12059888]

  pool = Pool(8)
  results = pool.map(__process_item, submit_ids)

  pool.close()
  pool.join()

  print("Finished")
  print("Total banned users detected: " + str(sum(results)))

run_job()

