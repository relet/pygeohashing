#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""meetupchart fetches all expeditions from the wiki (unless they are available in the meetupchart.data file)
   dumps them to meetupchart.data
   identifies expedition participants using more magick
   and generates shoebot code to display a xkcd#657-style graph of the expeditions
"""

import datetime, wikipedia, re, sys, yaml
from random import random
from catlib import Category
from UserListGenerator import getSection, identifyParticipants, getDebugFuzz

DATEFORMAT = "%Y-%m-%d"
RE_EXP  = re.compile("^\d{4}-\d{2}-\d{2} -?\d{1,3} -?\d{1,3}$")

ROW  = 10
COL  = 5 
FONT = 10
MIN_EXPEDITIONS = 5

def dump(filename, data):
  yamldump = open(filename,'w')          # store the data set we have last been working on
  yamldump.write(yaml.dump(data))   # in order to quickly identify changes in the future.
  yamldump.close()

def load(filename):
  yamldump = open(filename,'r')          # store the data set we have last been working on
  data = yaml.load(yamldump.read())   # in order to quickly identify changes in the future.
  yamldump.close()
  return data

def distance(place1, place2):
  lat1, lon1 = map(int,place1.split()) # that will ignore -0 issues
  lat2, lon2 = map(int,place2.split()) # but then, hashes behave strangely there anyway
  return abs(lon2-lon1)*1.5 + abs(lat2-lat1)

def resortPlacesByDistance(places):
  resorted = []
  last = []
  place1 = "999 -999" 
  last.append(place1)
  while len(places)>0:
    mindist = 99999
    best = None
    for place in places:
      dist = reduce(lambda x,y:x+y, map(lambda x:distance(x,place), last))
      if dist<mindist:
        mindist = dist
        best = place
    last.append(best)
    resorted.append(best)
    places.remove(best)
    if len(last)>5:
      last.pop(0)
  return resorted
    
site = wikipedia.getSite()

meta = Category(site, "Category:Meetup by location")
locations = meta.subcategories()

data = []
try:
  data = load("meetupchart.data")
  pass
except:
  print "No meetup chart data is available. We'll have to fetch everything from the wiki. This will take a good while."
  pass
  
if not data:
  for location in locations:
    pages = location.articlesList()
    for page in pages:
      title = page.title()
      if not RE_EXP.match(title):
        continue
      date = title[:10]
      latlon = title[11:]
      try:
        text = page.get()
      except: #skip redirects
        continue
      if "[[Category:Retro meetup]]" in text:
        continue
      if "[[Category:Not reached - Did not attempt]]" in text:
        continue
      if "[[Category:Expedition planning]]" in text:
        continue
      users = identifyParticipants(text, page)
      
      hadthese = []
      for user in users:
        if "/" in user:
          continue
        if user.lower() in hadthese:
          continue
        hadthese.append(user.lower())
        data.append((user, date, latlon))
      print title, hadthese, getDebugFuzz()
    dump("meetupchart.data",data) #keep backing it up, you'll never know...

people   = {}
places   = []
earliest = "9999"
latest   = "0000"

hadthese = []
for event in data:
  if event in hadthese:
    continue
  hadthese.append(event)
  peop, date, grat = event
  if date < "2008-05":
    continue
  if peop.lower().strip() in people:
    people[peop.lower().strip()].append(event)
  else:
    people[peop.lower()]=[event]
  if not grat in places:
    places.append(grat)
  if date<earliest:
    earliest=date
  if date>latest:
    latest=date

#print earliest
#sys.exit(1)

duration = (datetime.datetime.strptime(latest, DATEFORMAT) - datetime.datetime.strptime(earliest, DATEFORMAT)).days
girth = len(places)

places.sort(cmp = lambda x,y:cmp(int(x[x.index(" ")+1:]),int(y[y.index(" ")+1:])))

places = resortPlacesByDistance(places)

def xy (day, place):
  """ transform coordinates from date/place to pixel x,y """
  global earliest, places, DATEFORMAT
  
  days = (datetime.datetime.strptime(day, DATEFORMAT) - datetime.datetime.strptime(earliest, DATEFORMAT)).days
  return (50+days * COL, ROW+places.index(place) * ROW)
  
print("size(%i,%i)" % (100+duration * COL, ROW+girth*ROW))
print("nofill()")
print("stroke(0)")
print("font('NotCourier-sans', %i)" % (FONT))

for place in places:
  print("text(\"%s\", 5, %i)" % (place, xy(earliest, place)[1]+4))
   
for peop in people.keys():
  events = people[peop]
  if len(events)< MIN_EXPEDITIONS:
    continue
  events.sort(cmp = lambda x,y:cmp(x[1],y[1]))
  lastx, lasty = xy(events[0][1], events[0][2])  

  print("stroke(%f, %f, %f)" % (random()*3/4, random()*3/4, random()*3/4)) #avoid full white
  print("text(\"+%s\", %i, %i)" % (events[0][0].encode("utf-8"), lastx, lasty-3))
  print("oval(%i,%i,3,3)" % (lastx-1,lasty-1))
  print("beginpath(%i,%i)" % (lastx, lasty))
  for event in events[1:]:
    x,y = xy(event[1],event[2])
    if abs(y-lasty)>300:
      print("text(\"%s\", %i, %i)" % (events[0][0].encode("utf-8"), x, y+10))
    x1,y1 = lastx + (x-lastx)/2, lasty
    x2,y2 = lastx + (x-lastx)/2, y
    print("curveto(%i,%i,%i,%i,%i,%i)" % (x1,y1,x2,y2,x,y))
    print("oval(%i,%i,3,3)" % (x-1,y-1))
    lastx, lasty = x,y
  print("moveto (%i,%i)" % xy(events[0][1], events[0][2]))
  print("endpath()")
  print("text(\"-%s\", %i, %i)" % (events[-1][0].encode("utf-8"), lastx, lasty-3))
  
