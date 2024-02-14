#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""meetupchart fetches all expeditions from the wiki (unless they are available in the meetupchart.data file)
   dumps them to meetupchart.data
   identifies expedition participants using more magick
   and generates shoebot code to display a xkcd#657-style graph of the expeditions
"""

import datetime, wikipedia, re, sys, yaml, urllib
from random import random
from catlib import Category
from UserListGenerator import getSection, identifyParticipants, getDebugFuzz
from GraticuleDatabase import GraticuleDatabase

DATEFORMAT = "%Y-%m-%d"
RE_EXP  = re.compile("^\d{4}-\d{2}-\d{2} -?\d{1,3} -?\d{1,3}$")

ROW  = 10
COL  = 5 
FONT = 10
LEFTMARGIN = 300
RIGHTMARGIN = 50
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
    if len(last)>10:
      last.pop(0)
  return resorted

graticules = GraticuleDatabase()

def gratName(place):
  lat, lon = place.split(" ")
  return graticules.getLatLon(lat, lon)[0]
    
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
  
# these are the ones we can't fix currently
addfails  = [("John", "2008-06-07", "30 -84")]
skipfails = [("NWoodruff", "2009-08-31", "50 11"), 
             ("archchancellor", "2008-06-01", "37 -121"),
             ("Tom Wuttke", "2008-06-16", "37 -122"),
             ("Danatar", "2008-08-26", "51 7")]
  
if not data:
  data.extend(addfails)
  for location in locations:
    if "50 -1" in str(location):
      continue
    pages = list(location.articles())
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
        if (user, date, latlon) in skipfails:
          continue
        hadthese.append(user.lower())
        data.append((user, date, latlon))
      print title, hadthese, getDebugFuzz()
    dump("meetupchart.data",data) #keep backing it up, you'll never know...

userlist = urllib.urlopen("http://wiki.xkcd.com/wgh/index.php?title=Special:Listusers&limit=5000").read().lower()
users = re.findall("title=\"user:(.*?)\"", userlist)

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
  peop = peop.lower().strip().replace("_"," ")
  #if not peop.replace("&","&amp;") in users:
    #print "%s is no user" % peop.encode("utf-8")
  #  continue
  if peop in people:
    people[peop].append(event)
  else:
    people[peop]=[event]
  if not grat in places:
    places.append(grat)
  if date<earliest:
    earliest=date
  if date>latest:
    latest=date

duration = (datetime.datetime.strptime(latest, DATEFORMAT) - datetime.datetime.strptime(earliest, DATEFORMAT)).days
girth = len(places)

places.sort(cmp = lambda x,y:cmp(int(x[x.index(" ")+1:]),int(y[y.index(" ")+1:])))

places = resortPlacesByDistance(places)

def xy (day, place):
  """ transform coordinates from date/place to pixel x,y """
  global earliest, places, DATEFORMAT
  
  days = (datetime.datetime.strptime(day, DATEFORMAT) - datetime.datetime.strptime(earliest, DATEFORMAT)).days
  return (LEFTMARGIN+days * COL, ROW+places.index(place) * ROW)
  
w,h = LEFTMARGIN+RIGHTMARGIN+duration * COL, ROW+girth*ROW
  
print("size(%i,%i)" % (w,h))
print("nofill()")
print("stroke(0)")
print("font('NotCourier-sans', %i)" % (FONT))

for place in places:
  print("text(\"%s\", 5, %i)" % (place, xy(earliest, place)[1]+4))

print("stroke(.7,.7,.7)")
print("strokewidth(.5)")
day = datetime.datetime.strptime(earliest, DATEFORMAT)
while day <= datetime.datetime.strptime(latest, DATEFORMAT):
  if day.day == 1:
    x,y = xy(datetime.datetime.strftime(day, DATEFORMAT), places[0])
    print("text(\"%s/%s\",%i,%i)" % (str(day.month), str(day.year), x+3-COL/2, 10))
    print("beginpath(%i,%i)" % (x-COL/2, 0))
    print("lineto(%i,%i)" % (x-COL/2, h))
    print("endpath()")
  day += datetime.timedelta(1)

for i,place in enumerate(places):
  x,y = xy(earliest, place)
  if (i % 5) == 3:
    print("stroke(.85,.85,.85)")
    print("strokewidth(%i)" % ROW)
    print("beginpath(%i,%i)" % (48, y-ROW))
    print("lineto(%i,%i)" % (w, y-ROW))
    print("endpath()")
  if i>0 and distance(places[i],places[i-1]) > 50: # draw horizontal separators between far-away graticules
    print("stroke(.7,.7,.7)")
    print("strokewidth(.5)")
    print("beginpath(%i,%i)" % (LEFTMARGIN, y-ROW/2))
    print("lineto(%i,%i)" % (w, y-ROW/2))
    print("endpath()")
for i,place in enumerate(places):
  x,y = xy(earliest, place)
  print("stroke(.6,.6,.6)")
  print("text(\"%s\", 50, %i)" % (gratName(place).encode("utf-8"),y+4))

print("strokewidth(1.2)")

labels = []
def putlabel(s,x,y,up=True):
  blocked = False
  for label in labels:
    if abs(label[0]-x)<50 and abs(label[1]-y)<ROW:
      blocked = True 
  if blocked:
    putlabel(s,x,y+(up and -ROW or ROW),up)
  else:
    labels.append((x,y))
    print("text(\"%s\", %i, %i)" % (s, x, y))

points = []
def putpoint(p, lvl=3):
  x, y = p
  for point in points:
    if (point[0]==x) and (point[1]==y):
      lvl = point[2]
      points.remove(point)
      break
  points.append((x,y,lvl+1))
  return lvl


for peop in people.keys():
  events = people[peop]
  if len(events)< MIN_EXPEDITIONS:
    continue
  events.sort(cmp = lambda x,y:cmp(x[1],y[1]))
  lastx, lasty = xy(events[0][1], events[0][2])  

  print("stroke(%f, %f, %f)" % (random()*3/4, random()*3/4, random()*3/4)) #avoid full white
  putlabel("+"+events[0][0].replace("\"","\\\"").encode("utf-8"), lastx, lasty-3)
  dia = putpoint((lastx, lasty))
  print("oval(%i,%i,%i,%i)" % (lastx-dia/2, lasty-dia/2, dia, dia))
  print("beginpath(%i,%i)" % (lastx, lasty))
  for i,event in enumerate(events[1:]):
    x,y = xy(event[1],event[2])
    if abs(y-lasty)>300 and i<len(events)-2:
      putlabel(events[0][0].replace("\"","\\\"").encode("utf-8"), x, y+10, up=False)
    x1,y1 = lastx + (x-lastx)/2, lasty
    x2,y2 = lastx + (x-lastx)/2, y    
    print("curveto(%i,%i,%i,%i,%i,%i)" % (x1,y1,x2,y2,x,y))
    dia = putpoint((x,y))
    print("oval(%i,%i,%i,%i)" % (x-dia/2,y-dia/2, dia, dia))
    lastx, lasty = x,y
  print("moveto (%i,%i)" % xy(events[0][1], events[0][2]))
  print("endpath()")
  putlabel("-"+events[-1][0].replace("\"","\\\"").encode("utf-8"), lastx, lasty-3)
  
