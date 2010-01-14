#!/usr/bin/env python
# -*- coding: utf-8 -*-

import yaml, re, time, web
import xml.etree.ElementTree as ET

try:
  interesting = yaml.load(open("interesting.yaml", "r").read())
except:
  interesting = [
    ("New page", re.compile("New page"))
  ]

re_noenctags  = re.compile("&lt;.*?&gt;")
re_notags = re.compile("<.*?>")
re_noenc  = re.compile("&.*?;")

def setup(self):
  self.rcwatch={}

def rexlist(phenny, input): 
   for id, entry in enumerate(interesting):
     phenny.say("#%i: tag '%s' = pattern '%s'" % (id, entry[0], entry[1].pattern))
rexlist.commands = ['watchlist']
rexlist.priority = 'low'
rexlist.thread   = True

def rexadd(phenny, input): 
  if input.sender.startswith('#'): #this command only works in public
    try:
      line = input[input.index(" ")+1:]
      tag  = line[:line.index("=")]
      res  = line[line.index("=")+1:]
      rec   = re.compile(res, re.IGNORECASE)
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

def rexstart(phenny, input):  
  if "running" in phenny.rcwatch:
    phenny.say("Watch daemon is running already.") 
    return
  phenny.rcwatch["running"] = True

  phenny.msg("#geohashing", "Ok. Running the watch daemon.")

  oldrc = None
  try:
    oldrc = yaml.load(open("oldrc.yaml", "r").read())
  except:
    oldrc = "0"

  while True:
    time.sleep(60)
    
    if "stopme" in phenny.rcwatch:
      phenny.say("Aborted the watch daemon")
      del phenny.rcwatch["stopme"]
      return

    rc = web.get("http://wiki.xkcd.com/wgh/api.php?action=query&format=xml&list=recentchanges&rcprop=user|comment|flags|title|ids")
    if not rc:
      continue
    
    et = ET.fromstring(rc)
    
    newestcurrentid = "0"

    rclist = et.find("query").find("recentchanges")
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
      minor = "minor" in entry.keys()
      pageid = entry.get("pageid")
      
      if pageid in hadthese:
        continue
      hadthese.append(pageid)

      show = None
      for tag, re in interesting:
        if re.search(comment) or re.search(title) or re.search(user):
          show=tag
      if show!=None and minor==False:
        phenny.msg("#geohashing","News about \"%s\": http://geohashing.org/%s was edited by %s. (%s)" % (show, title, user, comment))
      elif new:
        phenny.msg("#geohashing","New page: http://geohashing.org/%s was created by %s. (%s)" % (title, user, comment))

    if newestcurrentid > oldrc:
      oldrc = newestcurrentid
    open("oldrc.yaml","w").write(yaml.dump(oldrc))
rexstart.commands = ['rcwatch']
rexstart.priority = 'low'
rexstart.thread   = True

def stopwatch(phenny, input): 
  phenny.rcwatch["stopme"]=True
  phenny.say("Ok. Daemon will be stopped.")
stopwatch.commands = ['stopwatch']
stopwatch.priority = 'high'
stopwatch.thread   = True
