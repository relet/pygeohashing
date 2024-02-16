#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Updates all graticule pages with a correct neighbour table. Creates new graticule pages for pages on All Graticules.

Syntax: python updateNeighbourGrats.py [lazy]
"""

#
# (C) Thomas Hirsch 2008-2009 - MIT License
#
import re, sys, os
import pywikibot, wikipedia
from GraticuleDatabase import GraticuleDatabase, inc, dec, grow

re_maprough  = '\{\{[gG]raticule[^\}]*lat= ?\+?%s?[^\}]*lon= ?\+?%s?[^\}]*?\}\}'
re_noedit = re.compile('\{\{[mM]aintained[^\}]*\}\}')

site = pywikibot.Site()

lazy = len(sys.argv)>1 and (sys.argv[1]=="lazy")

db = GraticuleDatabase()
new = db.getAllKeys()

all = []

if lazy:
  dbold = GraticuleDatabase("lastchangeset.sqlite")
  comp = dbold.getAllKeys()

  for grat in new:
    if grat in comp:
      if db.getLatLon(grat[0], grat[1]) == dbold.getLatLon(grat[0], grat[1]):
        continue
    all.extend(grow(grat))
  
else:
  all = new

for grat in all:
  lat, lon = grat
  data = db.getLatLon(lat, lon)
  if data:
    text = None
    try:
      page = wikipedia.Page(site, data[0])
      while page.isRedirectPage():
        page = page.getRedirectTarget()
        print(data[0],"redirected to",page)
      text = page.get()
    except:
      pass
    if text:
      if re_noedit.findall(text):
        print (u"Skipping page %s: Maintained" % data[0]).encode("utf-8")
        continue
      re_map = re.compile(re_maprough % (grat[0], grat[1]), re.DOTALL)
      match = re_map.findall(text)
      if match:
        statusquo  = match[0]
        suggestion = db.getTemplate(lat, lon, data[2])
        newtext = text.replace(statusquo, suggestion)
        if suggestion == statusquo:
          pass
        else:
          print (u"=== Old template text ========").encode("utf-8")
          print (u'Page: %s\n' % data[0]).encode("utf-8")
          print (statusquo).encode("utf-8")
          print (u"=== Replacement suggestion ===").encode("utf-8")
          print (suggestion).encode("utf-8")
          print (u"").encode("utf-8")
          confirm = wikipedia.input(u'Confirm? [y/n]> ')
          if confirm != "n":
            page.put(newtext, u"Updated graticule template with information from [[All Graticules]], using standard format.")
            print ("Ok.")
          else:
            print ("Skip.")
      else: 
        print (u'THERE IS NO MATCHING TEMPLATE ON PAGE %s!!!11!1' % data[0]).encode("utf-8")
    else:
      print(u'Page %s does not exist yet! We have to create it.' % data[0]).encode("utf-8")
      newtext = db.getTemplate(lat, lon, data[2])
      newtext += "\nThis graticule is located at [[%s,%s]]. [http://irc.peeron.com/xkcd/map/map.html?lat=%s&long=%s&zoom=9&abs=-1 Today's location]" % (lat, lon, lat, lon) 
      newtext += "\n\n[[Category:Inactive graticules]] [[Category:%s]]" % data[2]
      print (newtext).encode("utf-8")
      print (u"Also creating redirect:").encode("utf-8")
      print (u"Page: "+lat+","+lon+"\tText: #REDIRECT [["+data[0]+"]]").encode("utf-8")
      confirm = wikipedia.input(u'Confirm? [y/n]> ')
      if confirm != "n":
        page.put(newtext, u"Created inactive graticule page with information from [[All Graticules]], using standard format.")
        pagered = wikipedia.Page(site,lat+","+lon)
        pagered.put(u"#REDIRECT [["+data[0]+"]]", u"Created redirect for inactive graticule listed on [[All Graticules]].")
        print ("Ok.")
      else:
        print ("Skip.")
  else:
    print("Dataset for %s,%s not found" % (lat, lon))
    
print("Now dumping the database, to possibly improve the speed of the next run.")    
db.dump()
os.rename("graticules.sqlite", "lastchangeset.sqlite")
print("Done.")
