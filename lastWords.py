
import codecs
import http.client
import json
import ssl
import threading

from multiprocessing import Pool
from urllib.request import urlopen

"""Script to print the last comments of Hacker News users before they are banned.
Reads from the Hacker News API: https://github.com/HackerNews/API)

This is my first time writing python. Feedback is welcome.
"""

# Global variables
_DECODER = codecs.getreader("utf-8")
# To prevent SSL failure after too many calls.
_CONTEXT = ssl._create_unverified_context()
_LOCK = threading.Lock()
# _BAN_THRESHOLD_SECONDS = 3 days
# Bigger values increases false positives. 
# Examples: Recently unbanned users or https://news.ycombinator.com/item?id=12051001
# Smaller value misses the case for 10551997
_BAN_THRESHOLD_SECONDS = 60 * 60 * 24 * 3
_MOD_NAME = "dang"
  # Increasing the number of threads beyond 8 on my machine causes Http errors.
_MAX_NUM_THREADS = 8

DEBUG = False

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
  """Checks if mod wrote a comment to announce a ban.
  Args:
      data: json item from Hacker News.
  Returns:
      Returns true if the comment text contains the word "banned".
  """
  return __is_comment(data) \
    and "banned" in data["text"] \
    and "parent" in data

def __is_user_banned(user_comment, mod_comment):
  """Checks if the user is banned.

  Checks the timestamp of the last submitted item from the user.
  If the time is _BAN_THRESHOLD_SECONDS after the mod's comment then the user is still active.

  Args:
      user_comment: json item representing the user's comment.
      mod_comment: json item representing the mod's comment
  Returns:
      Returns true if the user is banned.
  """
  if __is_comment(user_comment) is False:
    return False  

  user_data = __get_user(user_comment["by"])
  recent_comment = __get_comment(user_data["submitted"][0])

  if DEBUG:
    print("Time delta: " + str(mod_comment["time"] - recent_comment["time"]))

  return mod_comment["time"] > recent_comment["time"] - _BAN_THRESHOLD_SECONDS

def __write_to_file(comment):
    _LOCK.acquire()
    with open("README.md", 'a') as out:
      # remove escape characters
      comment_text = comment["text"].replace("&#x2F;", "/")
      comment_text = comment_text.replace("&#x27;", "'")
      comment_text = comment_text.replace("&quot;", "\"")

      out.write("*\"" + comment_text + "\"*" + "\n")
      out.write("  [--" + comment["by"] + "](https://news.ycombinator.com/user?id=" + comment["by"] + ")\n\n\n")
    _LOCK.release()

def __process_item(id):
  """Checks if the parent user is banned and writes their last comment to file.
  Determins if the mod's comment is a ban announcment.
  If yes then check the user to see if they are banned.
  Write the user's last comment to file if they are banned.
  Last comment is defined as the parent comment of the mod's comment,
  which might not be the last submitted item from the user.

  Args:
      id: Id for Hacker News API.
  """
  if DEBUG:
    print("Processing: " + str(id))

  mod_comment = __get_comment(id)

  if __is_possible_ban(mod_comment):
    parent_comment = __get_comment(mod_comment["parent"])

    if __is_user_banned(parent_comment, mod_comment):
      __write_to_file(parent_comment)
    return 1

  return 0

def run_job():
  """Main function of the script
  Gets Id of all comments of the mod. Use a thread pool to fetch the json data for each Id.
  Then check if item is related to a banned user.
  """
  mod_data = __get_user(_MOD_NAME)
  submit_ids = mod_data["submitted"]
  # Uncomment for test data.
  #submit_ids = [10551997, 7867166, 12041458, 12059888, 11631519]

  pool = Pool(_MAX_NUM_THREADS)
  results = pool.map(__process_item, submit_ids)
  pool.close()
  pool.join()

  print("Finished")
  print("Total banned users detected: " + str(sum(results)))

run_job()
