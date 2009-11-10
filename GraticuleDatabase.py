#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, sys, yaml
import wikipedia

re_grat = re.compile('\[\[(.*?)\| *([0-9\-]+, *[0-9\-]+) *\(.*?\) *\]\]')

def inc(num):
  if num == "-0":
    return "0"
  if num=="179":
    return "-179"
  elif num == "-1":
    return "-0"
  else:
    return(str(int(num)+1))

def dec(num):
  if num=="-179":
    return "179"
  elif num=="0":
    return "-0"
  else:
    return(str(int(num)-1))

def grow(latlon):
  lat, lon = latlon
  return [(dec(lat), dec(lon)),
          (dec(lat), lon),
          (dec(lat), inc(lon)),
          (lat, dec(lon)),
          (lat, lon),
          (lat, inc(lon)),
          (inc(lat), dec(lon)),
          (inc(lat), lon),
          (inc(lat), inc(lon))]
          
class GraticuleDatabase:
    '''
    This is a hashtable of graticules indexed lat->lon->(name, country)
    '''
    def __init__(self, filename = None):
      if filename:
        self.load(filename)
      else:
        site = wikipedia.getSite()
        page = wikipedia.Page(site, u"All Graticules")
        text = page.get(get_redirect = False)
      
        self.data = {}
        result = re_grat.findall(text)
        for match in result:
          page, grat = match
          lat, lon = grat.split(", ")
          if not lat in self.data:
            self.data[lat]={}
          if grat in page:
            name = page
            country = reduce(lambda x,y:x+" "+y, page.split(" ")[0:-2])
          elif "," in page:
            cut = page.split(", ")
            name = cut[0]
            country = cut[-1]
          else:
            name = page
            country = None
          self.data[lat][lon] = (page, name, country)

    def dump(self, filename):
      yamldump = open(filename,'w')          # store the data set we have last been working on
      yamldump.write(yaml.dump(self.data))   # in order to quickly identify changes in the future.
      yamldump.close()

    def load(self, filename):
      yamldump = open(filename,'r')          # store the data set we have last been working on
      self.data = yaml.load(yamldump.read())   # in order to quickly identify changes in the future.
      yamldump.close()

    def getLatLon(self, lat, lon):
      try:
        return self.data[lat][lon]
      except:
        return ("%s,%s" % (lat,lon))

    def getAllKeys(self):
      all = []
      for lat in self.data.keys():
        for lon in self.data[lat].keys():
          all.append((lat,lon))
      return all

    def getAllWaterKeys(self):
      all = []
      for lat in self.data.keys():
        for lon in self.data[lat].keys():
          if lat+", "+lon in self.data[lat][lon][0]:
            all.append((lat,lon))
      return all

    def gratlink(self, lat, lon, refcountry = None):
      entry = self.getLatLon(lat, lon)
      if entry:
        page, name, country = entry
        link = page
        if country == refcountry:
          title = name.strip()
        elif country:
          title = name+", "+country.strip()
        else:
          title = name.strip()
        if lat in page:
          title = (page.split(lat)[0]).strip()
        if link == title:
          return "[[%s]]" % link
        else:
          return "[[%s|%s]]" % (link, title)
      else:
        return "[[%s,%s]]" % (lat, lon) 
      

    def getTemplate(self, lat, lon, refcountry):
      str = u'{{graticule\n'
      str += '   | lat= %s\n' % lat
      str += '   | lon= %s\n' % lon
      str += "   | nw = %s\n" % self.gratlink(inc(lat),dec(lon),refcountry)
      str += "   | n  = %s\n" % self.gratlink(inc(lat),lon,refcountry)
      str += "   | ne = %s\n" % self.gratlink(inc(lat),inc(lon),refcountry)
      str += "   | w  = %s\n" % self.gratlink(lat,dec(lon),refcountry)
      str += "   | name = %s\n" % self.gratlink(lat,lon,refcountry)
      str += "   | e  = %s\n" % self.gratlink(lat,inc(lon),refcountry)
      str += "   | sw = %s\n" % self.gratlink(dec(lat),dec(lon),refcountry)
      str += "   | s  = %s\n" % self.gratlink(dec(lat),lon,refcountry)
      str += "   | se = %s\n" % self.gratlink(dec(lat),inc(lon),refcountry)
      str += "}}"
      return str
