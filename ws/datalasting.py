#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""datalasting 
     - [ ] fetches all expeditions from the wiki
     - [ ] unless they exist in the database
     - [ ] may be run to work on certain dates only (specify a subcategory "Meetup on/in ..")
     - [ ] writes them into the reports table
"""

import datetime, wikipedia, re, sys, yaml, urllib
from catlib import Category
try:
  import pgsql as db
except:
  import psycopg2 as db

DATEFORMAT = "%Y-%m-%d"
RE_EXP  = re.compile("^\d{4}-\d{2}-\d{2} -?\d{1,3} -?\d{1,3}$")

update = False

site = wikipedia.getSite()
CONF = "/opt/geo/geo.conf"
host, dbname, user, password = open(CONF, "r").read().strip().split(",")

conn = db.connect(host=host, database=dbname, user=user, password='\''+password+'\'')
cur  = conn.cursor()

subcat = "Category:Meetup by date"
try: 
    args = sys.argv[1:]
    if "update" in args:
      update = True
    for arg in args:
      if "Category:" in arg:
        subcat = arg 
except Exception, ex:
    print ex
    pass

def recurseCategory(cat):
  subcats = cat.subcategories()
  for sub in subcats:
    recurseCategory(sub)
  for exp in cat.articles():
      print "handling article ",exp
      title = exp.title()
      if not RE_EXP.match(title):
        print "exp match failed."
        continue
      date = title[:10]
      lat,lon = [x.strip() for x in title[11:].split()]

      cur.execute("select * from reports where title = '%s'" % title)
      if cur.fetchone():
        if not update:
          print "contained in database."
          continue
        else:
          cur.execute("delete from categories where title = '%s'" % title)
          cur.execute("delete from participants where title = '%s'" % title)
          cur.execute("delete from reports where title = '%s'" % title)
          conn.commit()
      
      try:
        text = exp.get()
      except: #skip redirects
        print "is redirect."
        continue
      if "[[Category:Retro meetup]]" in text:
        print "is retro."
        continue
      if "[[Category:Not reached - Did not attempt]]" in text:
        print "was not attempted."
        continue
      if "[[Category:Expedition planning]]" in text:
        print "is planning."
        continue

      cur.execute("insert into reports values ('%s', '%s')" % (title.replace("'","''"), text.replace("'","''")))
      conn.commit()
      print "inserted", title

meta = Category(site, subcat)
recurseCategory(meta)
