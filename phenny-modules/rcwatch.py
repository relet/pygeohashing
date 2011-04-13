#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml, re, time, web, sys
import urllib
import xml.etree.ElementTree as ET
import random

channel = "#geohashing"
sleepytime = 60

try:
  interesting = yaml.load(open("interesting.yaml", "r").read())
except:
  interesting = [
    ("New page", re.compile("New page"))
  ]
try:
  re_spam = yaml.load(open("spam.yaml", "r").read())
except:
  re_spam = []
try:
  lyrics = yaml.load(open("lyrics.yaml", "r").read())
except:
  lyrics = []

re_noenctags  = re.compile("&lt;.*?&gt;")
re_notags = re.compile("<.*?>")
re_noenc  = re.compile("&.*?;")
re_anonymous = re.compile("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")


def rexlist(phenny, input): 
   for id, entry in enumerate(interesting):
     phenny.say("#%i: tag '%s' = pattern '%s'" % (id, entry[0], entry[1].pattern))
rexlist.commands = ['watchlist']
rexlist.priority = 'low'
rexlist.thread   = True

def spamlist(phenny, input): 
   for id, entry in enumerate(re_spam):
     phenny.say("#%i: pattern '%s'" % (id, entry.pattern))
spamlist.commands = ['spamlist']
spamlist.priority = 'low'
spamlist.thread   = True

def rexadd(phenny, input): 
  if input.sender.startswith('#'): #this command only works in public
    try:
      line = input[input.index(" ")+1:]
      tag  = line[:line.index("=")]
      res  = line[line.index("=")+1:]
      rec   = re.compile(res, re.IGNORECASE | re.DOTALL)
      interesting.append((tag,rec))
      open("interesting.yaml","w").write(yaml.dump(interesting))
      phenny.say("Notification installed. tag '%s' = pattern '%s'" % (tag, rec.pattern))
    except Exception, ex:
      phenny.say("Could not add this. %s" % str(ex))
  else:
    phenny.say("Please do this in a public channel.")
rexadd.commands = ['addwatch']
rexadd.example = ".addwatch badgers=[Bb]adger"
rexadd.priority = 'low'

def spamadd(phenny, input): 
  if input.sender.startswith('#') or input.sender == "relet": #this command only works in public
    try:
      line = input[input.index(" ")+1:]
      res  = line.strip()
      rec   = re.compile(res, re.IGNORECASE)
      re_spam.append(rec)
      open("spam.yaml","w").write(yaml.dump(re_spam))
      phenny.say("Spam trigger installed. pattern '%s'" % (rec.pattern))
    except Exception, ex:
      phenny.say("Could not add this. %s" % str(ex))
  else:
    phenny.say("Please do this in a public channel.")
spamadd.commands = ['addspam']
spamadd.example = ".addspam growth hormones"
spamadd.priority = 'low'

def testspam(phenny, input):
  try:
    for re in re_spam:
      if re.search(input):
        phenny.say("%s matches." % re.pattern)
  except Exception,ex:
    phenny.say("There is a fail: %s" % str(ex))
testspam.commands=["testspam"]
testspam.priority="low"

lyricsenders = []
def addlyrics(phenny, input):
  global lyrics
  if input.sender.startswith("#"):
    return
  if input==".endlyrics":
    try:
      lyricsenders.remove(input.nick)
      phenny.say("Thank you!")
    except:
      phenny.say("Hmm. Are you sure you used the .lyrics command first?")
    return
  if input[:7]==".lyrics":
    lyricsenders.append(input.nick)
    phenny.say("Ok. Go ahead. Send me a .endlyrics when you're done, or I'm going to publish everything you say on the Internet. I mean it.")
    return
  if input.nick in lyricsenders:
    lyrics.append(input.strip())
    open("lyrics.yaml","w").write(yaml.dump(lyrics))
addlyrics.rule = r'.*'
addlyrics.priority = 'low'

def rexremove(phenny, input): 
  if input.sender.startswith('#'): #this command only works in public
    try:
      line = input[input.index(" ")+1:]
      id = int(line)
      tag, rec = interesting.pop(id)
      open("interesting.yaml","w").write(yaml.dump(interesting))
      phenny.say("Notification '%s' removed." % (tag))
    except Exception, ex:
      phenny.say("Could not remove this. %s" % str(ex))
  else:
    phenny.say("Please do this in a public channel.")
rexremove.commands = ['rmwatch']
rexremove.priority = 'low'

def spamremove(phenny, input): 
  if input.sender.startswith('#') or input.sender=="relet": #this command only works in public
    try:
      line = input[input.index(" ")+1:]
      id = int(line)
      rec = re_spam.pop(id)
      open("spam.yaml","w").write(yaml.dump(re_spam))
      phenny.say("Spam trigger %s removed." % (rec.pattern))
    except Exception, ex:
      phenny.say("Could not remove this. %s" % str(ex))
  else:
    phenny.say("Please do this in a public channel.")
spamremove.commands = ['rmspam']
spamremove.priority = 'low'

def rexstart(phenny, input):  
  if "running" in phenny.rcwatch:
    if ".rcwatch" in input:
      phenny.say("Watch daemon is running already.") 
    return
  phenny.rcwatch["running"] = True

  #phenny.msg(channel, "Ok. Running the watch daemon.")
  annoying = False

  oldrc = None
  try:
    oldrc = yaml.load(open("oldrc.yaml", "r").read())
  except:
    oldrc = "0"

  while True:
    time.sleep(sleepytime)
    
    if "stopme" in phenny.rcwatch:
      phenny.say("Aborted the watch daemon")
      del phenny.rcwatch["stopme"]
      return

    rc = None
    try:
      rc = web.get("http://wiki.xkcd.com/wgh/api.php?action=query&format=xml&list=recentchanges&rcprop=user|comment|flags|title|ids&rclimit=20")
    except:
      phenny.rcwatch["down"]=phenny.rcwatch.get("down",0)+1
      if phenny.rcwatch["down"]==3:
        phenny.msg(channel,"The wiki %s. \o/" % (random.choice(["has gone down.", "is no more.", "is unreachable.", "has disappeared.", "- I can't find it"])))
    if not rc:
      continue
    if "down" in phenny.rcwatch:
      if phenny.rcwatch["down"]>3:
        phenny.msg(channel,"The wiki is back!")
      del phenny.rcwatch["down"]
    
    et = ET.fromstring(rc)
    if not et:
      print "No page returned."
      return   
 
    newestcurrentid = "0"

    try:
      rclist = et.find("query").find("recentchanges")
    except Exception,ex:
      print ex
      continue 
    hadthese = []
    for entry in rclist:
      rcid = entry.get("rcid")
      if rcid > newestcurrentid:
        newestcurrentid = rcid
      if rcid <= oldrc:
        continue
      typ = entry.get("type")
      title = entry.get("title")
      user = entry.get("user")
      comment = entry.get("comment")
      new = "new" in entry.keys()
      bot = "bot" in entry.keys()
      minor = "minor" in entry.keys()
      pageid = entry.get("pageid")
      revid = entry.get("revid")
      
      if pageid in hadthese:
        continue
      hadthese.append(pageid)

      show, spam = None, None

      if re_anonymous.match(user):
        try:
          page = web.get("http://wiki.xkcd.com/wgh/index.php?title=%s&action=raw" % urllib.quote(title))
          for re in re_spam:
            if re.search(comment) or re.search(title) or re.search(page):
              spam = True
        except Exception, ex:
          print "while fetching page:"
          print ex #if it doesn't work, don't bother the channel. log it though.

      if "[Shmulik]" in comment:
        spam=False
        minor=True #prevent reporting, too

      if spam:
        try:
	  #login
          #result = web.post("http://wiki.xkcd.com/wgh/api.php", {"action":"login", "lgname":"ReletBot", "lgpassword":"...", "format":"xml"})
          #result might be a fail, most frequently because we are being throttled.
          #get rollback token
          rvpage = web.post("http://wiki.xkcd.com/wgh/api.php", {"action":"query", "titles":title, "prop":"info", "intoken":"edit", "format":"xml"})
          et2 = ET.fromstring(rvpage)
	  try:
            info = et2.find("query").find("pages").find("page")
	    token = info.get("edittoken")
            rvcheck = info.get("lastrevid")
            if rvcheck != revid:
              print "Someone else seems to have reverted this spam. (%s,%s)" % (title, revid) 
	      continue
          except Exception,ex:
            print "while fetching edit token:"
            print ex
            continue

          #get a lyric comment
          comment = "[Shmulik] "
          if len(lyrics)>0:
	    annoying = False
            comment+=lyrics.pop(0)
            open("lyrics.yaml","w").write(yaml.dump(lyrics))
          else:
	    comment+="undoing the last edit, because I think it looks like spam."
          if len(lyrics)==10:
            phenny.msg(channel, "I'm running out of spam-undo-lyrics. Please send me some in a private message using the .lyrics command.")
          if len(lyrics)==0:
            if not annoying:
              phenny.msg(channel, "Oh no! I've run out of spam-undo-lyrics. Please do send me some lyrics in a private message using the .lyrics command.")
              annoying = True

          #undo spam
	  if typ=="new":
            result = web.post("http://wiki.xkcd.com/wgh/api.php", {"action":"edit", "title":title, "bot":"0", "text":"{{spam}}", "token":token, "summary":comment, "format":"xml"})
          else:
            result = web.post("http://wiki.xkcd.com/wgh/api.php", {"action":"edit", "title":title, "undo":rvcheck, "bot":"0", "token":token, "summary":comment, "format":"xml"})

        except Exception, ex:
          print "while undoing:"
          print ex #if it doesn't work, don't bother the channel. log it though.
        continue #do not announce the page if it is spam!
      
      else:
        for tag, re in interesting:
          if re.search(comment) or re.search(title) or re.search(user):
            show=tag
        if show!=None and minor==False:
          if "[live]" in comment:
            phenny.msg(channel,"%s: %s (http://geohashing.org/%s)" % (user, comment, title.replace(' ','_')))
          else:
            phenny.msg(channel,"\"%s\": http://geohashing.org/%s was edited by %s. (%s)" % (show, title.replace(' ','_'), user, comment))
        elif new and (not bot) and (not minor):
          phenny.msg(channel,"New page: http://geohashing.org/%s was created by %s. (%s)" % (title.replace(' ','_'), user, comment))

    if newestcurrentid > oldrc:
      oldrc = newestcurrentid
    open("oldrc.yaml","w").write(yaml.dump(oldrc))
rexstart.rule = r'.*'
rexstart.priority = 'low'
rexstart.thread   = True 

def setup(self):
  self.rcwatch={}

def stopwatch(phenny, input): 
  phenny.rcwatch["stopme"]=True
  phenny.say("Ok. Daemon will be stopped.")
stopwatch.commands = ['stopwatch']
stopwatch.priority = 'high'
stopwatch.thread   = True
