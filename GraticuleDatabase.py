#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re, sys
import pywikibot
import sqlite3
import functools

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
      if not page:
        page = ""
      if not name:
        name = ""
      if not country:
        country = ""
      ex_string = 'insert or replace into graticules values ("' + lat + '","' + lon + '","'
      try:
        ex_string += page.decode("utf-8")
      except:
        ex_string += page
      ex_string += '","'
      try:
        ex_string += name.decode("utf-8")
      except:
        ex_string += name
      ex_string += '","'
      try:
        ex_string += country.decode("utf-8")
      except:
        ex_string += country
      ex_string += '","'
      if iswater:
        ex_string += "TRUE\")"
      else:
        ex_string += "FALSE\")"
      self.cur.execute(ex_string) #encode to utf-8 here?
      self.db.commit()

    def parseGraticulePage(self, page):
      text = page.get(get_redirect = False)
      
      result = re_grat.findall(text)
      num_results = len(result)
      cur_match = 0
      for match in result:
        page, grat = match
        lat, lon = grat.split(", ")
        if grat in page:
          name = page
          country = functools.reduce(lambda x,y:x+" "+y, page.split(" ")[0:-2])
        elif "," in page:
          cut = page.split(", ")
          name = cut[0]
          country = cut[-1]
        else:
          name = page
          country = None
        cur_match = cur_match + 1
        pywikibot.output("Adding Graticule " + str(cur_match) + " of " + str(num_results) + " : " + page)
        self.addGraticule( lat, lon, page, name, country )

    def __init__(self, filename = None):
      if filename:
        self.load(filename)
      else:
        site = pywikibot.getSite()
        self.load("graticules.sqlite")
        self.parseGraticulePage(pywikibot.Page(site, u"All graticules/Eurasia"))
        self.parseGraticulePage(pywikibot.Page(site, u"All graticules/Australasia"))
        self.parseGraticulePage(pywikibot.Page(site, u"All graticules/Africa"))
        self.parseGraticulePage(pywikibot.Page(site, u"All graticules/North America"))
        self.parseGraticulePage(pywikibot.Page(site, u"All graticules/South America"))
        self.parseGraticulePage(pywikibot.Page(site, u"All graticules/Oceans"))
        self.parseGraticulePage(pywikibot.Page(site, u"All graticules/Antarctica"))

    def dump(self):
      self.db.commit()

    def load(self, filename):
      self.db = sqlite3.connect(filename)
      self.cur = self.db.cursor()
      self.cur.execute ('create table if not exists graticules (lat text, lon text, page text, name text, country text, water boolean)')
      self.cur.execute ('create index if not exists klatlon on graticules (lat, lon)')
      self.cur.execute ('create index if not exists kwater on graticules (water)')
      self.db.commit()

    def getLatLon(self, lat, lon, unknownIsNumeric = False):
      try:
        execute_text = 'select page, name, country from graticules where lat = \'' + lat + "' and lon = '" + lon + "'" 
        self.cur.execute(execute_text)
        page, name, country = self.cur.fetchone()
        return (page, name, country)
      except:
        if unknownIsNumeric:
          return ("%s,%s" % (lat,lon))
        else:
          return None
          
    def findAll(self, search):
      cur.execute('select lat,lon,page from graticules where page like %s', "%"+search+"%")
      return cur.fetchall()

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
