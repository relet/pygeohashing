# -*- coding: utf-8 -*-

import re, web, datetime, hashlib, struct, yaml, sys, wikipedia
import xml.etree.ElementTree as ET

re_NUMERIC  = re.compile("(-?\d+)[ ,]+(-?\d+)")
re_NUMERICF = re.compile("(-?[\.\d]+)[ ,]+(-?[\.\d]+)") #fractions allowed
re_EXPEDITION = re.compile('\[\[(\d{4}-\d{2}-\d{2} -?\d+ -?\d+)')

def getdjia(date):
  try:
    return web.get("http://geo.crox.net/djia/%s" % date)
  except:
    return None

def geohash(djia, date):
  sum = hashlib.md5("%s-%s" % (date, djia)).digest()
  lat, lon = [x/2.**64 for x in struct.unpack_from(">QQ", sum)];
  return lat, lon

def exp2latlon(expstring): #parameter: a string in the expedition format yyyy-mm-dd lll lll
  sdate, lat, lon = expstring.split()
  date = datetime.datetime.strptime(sdate,"%Y-%m-%d").date()
  if int(lon)>-30 and date > datetime.date(2008,05,26): 
    date = date - datetime.timedelta(1) #use the previous day for W30
  djia = getdjia(date)

  if not djia:
    print ("Could not retrieve DJIA for %s." % date)
    return
  if "not available" in djia:
    print ("DJIA for %s not available yet." % date)
    return
  if "error" in djia:
    print ("crox reported an error while retrieving DJIA for %s." % date)
    return

  flat, flon = geohash(djia, sdate)
  geolat = lat + str(flat)[1:]
  geolon = lon + str(flon)[1:]
  
  return geolat, geolon

def geolookup(lat, lon):
  et = None
  result = {}
  try:
    bytes = web.get("http://ws.geonames.org/extendedFindNearby?lat=%s&lng=%s" % (lat,lon))
    et  = ET.fromstring(bytes)
  except:
    phenny.msg(renick, "geonames.org web services seem to be unavailable.")
    return
  s   = ""
  for item in et:
    if item.tag in ["geoname","ocean"]:
      ifcode = item.find("fcode")
      if ifcode!=None:
        result[ifcode.text] = item.find("name").text
    elif item.tag in ["country","continent"]:
      result[item.tag] = item.text
    elif item.tag == "address":
      result["streetNumber"] = item.find("streetNumber").text
      result["street"] = item.find("street").text
      result["postalcode"] = item.find("postalcode").text
      result["placename"] = item.find("placename").text
      result["adminName2"] = item.find("adminName2").text
      result["adminName1"] = item.find("adminName1").text
      result["countryCode"] = item.find("countryCode").text
    else:
      print "Unhandled tag: %s" % item.tag
  return result
  
site = wikipedia.getSite()

if len(sys.argv)>1:
  user = sys.argv[1]
else:
  print "usage:\n./regional username"
  sys.exit(1)

page = wikipedia.Page(site, "User:"+user)
data = page.get()
expeditions = re_EXPEDITION.findall(data)

regionals = {}

count = 0

for exp in expeditions:
  date, glat, glon = exp.split()
  lat, lon = exp2latlon(exp)
  place    = geolookup(lat,lon)
  print place
  for fcode, name in place.iteritems():
    if fcode:
      if not fcode in regionals:
        regionals[fcode]={}
      if not name in regionals[fcode]:
        regionals[fcode][name]={}
      regionals[fcode][name][glat+" "+glon]=True

for fcode, names in regionals.iteritems():
  for name, grats in names.iteritems():
    num = len(grats)
    print "%s %s - %i graticules" % (fcode, name, num)
    if num>3:
      for grat in grats:
        print grat+";",
      print
