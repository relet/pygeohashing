#!/usr/bin/env python
# -*- coding: utf-8 -*-
# READ-ONLY VERSION

import re, sys
#import wikipedia
import sqlite

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
    
    def addGraticule(self, lat, lon, page, name, country):
      iswater = lat+","+lon in name
      self.cur.execute('insert or replace into graticules values (%s,%s,%s,%s,%s,%s)', (lat, lon, page.encode("utf-8"), name and name.encode("utf-8"), country and country.encode("utf-8"), iswater and "TRUE" or "FALSE")) #encode to utf-8 here?
      self.db.commit()

    def parseGraticulePage(self, page):
      text = page.get(get_redirect = False)
      
      result = re_grat.findall(text)
      for match in result:
        page, grat = match
        lat, lon = grat.split(", ")
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
        self.addGraticule( lat, lon, page, name, country )

    def __init__(self, filename = None):
      if filename:
        self.load(filename)

    def dump(self):
      self.db.commit()

    def load(self, filename):
      self.db = sqlite.connect(filename)
      self.cur = self.db.cursor()
      self.cur.execute ('create table if not exists graticules (lat text, lon text, page text, name text, country text, water boolean)')
      self.cur.execute ('create index if not exists klatlon on graticules (lat, lon)')
      self.cur.execute ('create index if not exists kwater on graticules (water)')
      self.db.commit()

    def getLatLon(self, lat, lon, unknownIsNumeric = False):
      try:
        self.cur.execute('select page, name, country from graticules where lat = %s and lon = %s', (lat, lon))
        page, name, country = self.cur.fetchone()
        return (page.decode("utf-8"), name and name.decode("utf-8"), country and country.decode("utf-8"))
      except:
        if unknownIsNumeric:
          return ("%s,%s" % (lat,lon))
        else:
          return None
          
    def findAll(self, search):
      self.cur.execute('select lat, lon, page from graticules where page like %s', "%"+search+"%")
      return self.cur.fetchall()

    def getAll(self):
      self.cur.execute('select lat, lon, page from graticules')
      return self.cur.fetchall()

    def getAllKeys(self): 
      self.cur.execute('select lat, lon from graticules')
      return self.cur.fetchall()

    def getAllWaterKeys(self):
      self.cur.execute('select lat, lon from graticules where water = TRUE')
      return self.cur.fetchall()


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
          return u"[[%s]]" % link
        else:
          return u"[[%s|%s]]" % (link, title)
      else:
        return u"[[%s,%s]]" % (lat, lon)
      

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
