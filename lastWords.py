
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
# 3 days
_BAN_THRESHOLD_SECONDS = 60 * 60 * 24 * 3

DEBUG = True



def __get_user(id):
  return json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/user/"
      + id
      + ".json", 
      context=_CONTEXT)))

def __get_comment(id):
  return json.load(_DECODER(urlopen("https://hacker-news.firebaseio.com/v0/item/"
      + str(id)
      + ".json",
      context=_CONTEXT)))

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

def __is_user_banned(user_comment, mod_comment):
  if __is_comment(user_comment) is False:
    return False  

  user_data = __get_user(user_comment["by"])
  recent_comment = __get_comment(user_data["submitted"][0])

  # if mod comments and then bans then user, we might miss a few banned users due to race condition.
  if DEBUG:
    print(mod_comment["time"] - recent_comment["time"])
  return mod_comment["time"] > recent_comment["time"] - _BAN_THRESHOLD_SECONDS

def __process_item(id):
  if DEBUG:
    print("Processing: " + str(id))

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
    parent_comment = __get_comment(mod_comment["parent"])

    if __is_user_banned(parent_comment, mod_comment):
      _LOCK.acquire()
      with open("README.md", 'a') as out:
        out.write("*\"" + parent_comment["text"] + "\n" + "\"*" )
        out.write("  [--" + parent_comment["by"] + "](https://news.ycombinator.com/user?id=" + parent_comment["by"] + ")\n\n\n")
      _LOCK.release()
    return 1
  return 0

def run_job():
  mod_data = __get_user("dang")
  submit_ids = mod_data["submitted"]

  # Uncomment for test data
  submit_ids = [10551997, 7867166, 12041458, 12059888]

  pool = Pool(1)
  results = pool.map(__process_item, submit_ids)

  pool.close()
  pool.join()

  print("Finished")
  print("Total banned users detected: " + str(sum(results)))

run_job()

