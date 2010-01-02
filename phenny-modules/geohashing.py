# -*- coding: utf-8 -*-

import re, web, datetime, hashlib, struct, yaml
from GraticuleDatabase import GraticuleDatabase
import xml.etree.ElementTree as ET
import geohash as geohashorg

lazy = "../code/pywikipedia/lastchangeset.yaml"
db = GraticuleDatabase(lazy)

def setup(self):
  try: 
    f = open("geohashing.yaml","r")
    self.geohashing = yaml.load(f.read())
    f.close()
  except:
    self.geohashing = {}

def register(phenny, input):
  nick = input.nick
  data = phenny.geohashing.get(nick,[])
  words = input.split()
  reg  = (words[0] == '.register')
  lat, lon, place = identifyPlace(" ".join(words[1:]))
  if not lat:
    phenny.say("I don't know where that is.")
    return
  if reg:
    if (lat,lon) in data:
      phenny.say("You're already registered to receive updates for graticule %s,%s (%s)." % (lat,lon,place))
      return
    else:
      data.append((lat,lon))
      phenny.geohashing[nick] = data
      phenny.say("Ok. You will now receive updates for graticule %s,%s (%s)." % (lat,lon,place))
  else:
    if not (lat,lon) in data:
      phenny.say("You aren't currently registered to receive updates for graticule %s,%s (%s)." % (lat,lon,place))
      return
    else:
      data.remove((lat,lon))
      phenny.geohashing[nick] = data
      phenny.say("Ok. You will no longer receive updates for graticule %s,%s (%s)." % (lat,lon,place))
  f = open("geohashing.yaml","w")
  f.write(yaml.dump(phenny.geohashing))
  f.close()
register.commands = ['register', 'unregister']
register.priority = 'low'
register.thread = False

def gratrefresh(phenny, input):
  global db
  db = GraticuleDatabase()
  phenny.say("Ok, I should have it refreshed now.")
gratrefresh.commands = ['gratrefresh']
gratrefresh.priority = 'low'
gratrefresh.thread = True

re_NUMERIC  = re.compile("(-?\d+)[ ,]+(-?\d+)")
re_NUMERICF = re.compile("(-?[\.\d]+)[ ,]+(-?[\.\d]+)") #fractions allowed

def geohash(djia, date):
  sum = hashlib.md5("%s-%s" % (date, djia)).digest()
  lat, lon = [x/2.**64 for x in struct.unpack_from(">QQ", sum)];
  return lat, lon
  
def getdjia(date):
  try:
    return web.get("http://geo.crox.net/djia/%s" % date)
  except:
    try:
      y,m,d = str(date).split("-")
      return web.get("http://irc.peeron.com/xkcd/map/data/%s/%s/%s" % (y,m,d))
    except Exception,e:
      print date, e
      return None

def geoSearch(term):
  try:
    bytes = web.get("http://ws.geonames.org/search?q=%s&maxRows=1&lang=en" % (term))
    et  = ET.fromstring(bytes)
  except:
    return None
  for item in et:
    if item.tag != "geoname":
      continue
    name = item.find("name")
    cname = item.find("countryName")
    lat = item.find("lat")
    lon = item.find("lng")
    return (name != None) and (name.text != None) and name.text, (cname != None) and (cname.text != None) and cname.text, (lat != None) and (lat.text != None) and lat.text, (lon != None) and (lon.text != None) and lon.text #sorry.

def gratinfo(phenny, input):
  term = input
  try: 
    term = input[input.index(" ")+1:]
  except:
    phenny.say(".where's (lat,lon|query)")
    return
  found = re_NUMERIC.search(input)
  if found:
      lat, lon = found.groups(0)
      info = db.getLatLon(lat, lon, False)
      if not info:
        phenny.say("This seems to be an unnamed graticule.")
      else:
        phenny.say("That's %s! http://geohashing.org/%s,%s" % (info[0], lat, lon))
  else:
      grats = db.findAll(term)
      if grats:
        for grat in grats[:5]:
          phenny.say("There's %s at %s,%s. http://geohashing.org/%s,%s" % (grat[1][0], grat[0][0], grat[0][1], grat[0][0], grat[0][1]))
        if len(grats)>4:
          phenny.say("There's even more, but you have to be more specific.")
      else:
        phenny.say("Couldn't find a graticule of that name.")
        geo = geoSearch(term)
        print geo
        if geo and geo[0]:
          phenny.say("Did you mean %s at %s,%s?" % (geo[0]+(geo[1] and ", "+geo[1] or ""), geo[2], geo[3]))
  
gratinfo.commands = ['grat', 'where\'s', 'graticule']
gratinfo.priority = 'low'
gratinfo.thread = True

def appendTag(item, tag, sep, s):
  name = item.find(tag)
  if (name!=None) and (name.text != None):
    if len(s):
      s+=sep
    return s+name.text
  else:
    return s

def geolookup(phenny, input, renick=None):
  if not renick:
    if hasattr(input, 'sender'):
      renick = input.sender
    else:
      renick = '#geohashing'
  found = re_NUMERICF.search(input)
  if found:
    lat, lon = found.groups(0)
    et = None
    try:
      bytes = web.get("http://ws.geonames.org/extendedFindNearby?lat=%s&lng=%s" % (lat,lon))
      et  = ET.fromstring(bytes)
    except:
      phenny.msg(renick, "geonames.org web services seem to be unavailable.")
      return
    s   = ""
    for item in et:
      if item.tag in ["geoname","ocean"]:
        s = appendTag(item, "name", ", ", s)
      elif item.tag in ["country","continent"]:
        if len(s):
          s+=", "
        s+= item.text
      elif item.tag == "address":
        s = appendTag(item, "streetNumber", "", s)
        s = appendTag(item, "street", " ", s)
        s = appendTag(item, "postalcode", ", ", s)
        s = appendTag(item, "placename", " ", s)
        s = appendTag(item, "adminName2", ", ", s)
        s = appendTag(item, "adminName1", ", ", s)
        s = appendTag(item, "countryCode", ", ", s)
        s = appendTag(item, "distance", " - distance: ", s)
        if "distance" in s: 
          s+="km"
      else:
        print "Unhandled tag: %s" % item.tag
    if len(s):
      phenny.msg(renick, "Location: %s." % s)
    else:
      phenny.msg(renick, "I can't find this place.")
  else:
    phenny.msg(renick, ".lookup lat,lon")
geolookup.commands = ['lookup']
geolookup.priority = 'low'
geolookup.thread = True
  
def identifyPlace(string):
  lat, lon, place = None, None, None
  if string!="global":
    found = re_NUMERIC.search(string)
    if found:
      lat, lon = found.groups(0)
      place = lat+","+lon
    else: 
      namematch = db.findAll(string)
      if namematch:
        lat, lon = namematch[0][0][0], namematch[0][0][1]
        place = namematch[0][1][0]
      else: 
        geo = geoSearch(string)
        if geo:
          lat, lon = geo[2], geo[3]
          place = geo[0]+(geo[1] and ", "+geo[1] or "")
          if "." in lat: 
            lat = lat[:lat.index(".")]
            lon = lon[:lon.index(".")]
  return lat, lon, place
  
def hashes(phenny, input, renick=None):
  parts = input.split();
  lat, lon = None, None
  place = None
  if not renick:
    if hasattr(input, "sender"):
      renick = input.sender
    else:
      renick = "#geohashing"
  date  = datetime.date.today()
  try:
    if parts[1]=="help":
      phenny.msg(renick, ".# [place|\"global\" [date]]")
      return
    lat, lon, place = identifyPlace(parts[1])
    date = datetime.datetime.strptime(parts[2],"%Y-%m-%d").date()
  except:
    pass #keep to the defaults then
  sdate = str(date)
  if (lon==None) or ((int(lon)>-30) and (date > datetime.date(2008,5,26))): #only use previous day's coordinates after W30 has been invented.
      date = date - datetime.timedelta(1)
  djia = getdjia(date)
  if not djia:
    phenny.msg(renick, "Could not retrieve DJIA for %s." % sdate)
    return
  if "not available" in djia:
    phenny.msg(renick, "DJIA for %s not available yet." % sdate)
    return
  if "error" in djia:
    phenny.msg(renick, "crox reported an error while retrieving DJIA for %s." % sdate)
    return
  flat, flon = geohash(djia, sdate)
  if not lat:
    lat = str(flat * 180 - 90)
    lon = str(flon * 360 - 180)
    url = "http://geohash.org/%s" % geohashorg.encode(float(lat), float(lon))
    phenny.msg(renick, "Globalhash for %s is: %s, %s. %s" % (sdate, lat, lon, url))
  else:
    lat = lat + str(flat)[1:]
    lon = lon + str(flon)[1:]
    url = "http://geohash.org/%s" % geohashorg.encode(float(lat), float(lon))
    phenny.msg(renick, "Geohash for %s on %s is: %s, %s. %s" % (place, sdate, lat, lon, url))
  geolookup(phenny, "%s,%s" % (lat,lon), renick)
hashes.commands = ['#']
hashes.priority = 'low'
hashes.thread = True

re_DATE = re.compile('^(?:W30|All):.*?(\d{4}-\d{2}-\d{2})')

def zbotextra(phenny, input):
  match = re_DATE.search(input)
  if match:
    date = match.groups(0)[0]
    hashes(phenny, ".# global %s" % date, input.sender)
    if input.nick == 'zbot':
      for user, grats in phenny.geohashing.items():
        for grat in grats:
          lat, lon = grat
          hashes(phenny, ".# %s,%s %s" % (lat,lon,date), user)
    
zbotextra.thread = False
zbotextra.priority = 'low'
zbotextra.rule = r'^(W30|All):.*?(\d{4}-\d{2}-\d{2})'
