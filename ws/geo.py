#!/bin/env python
"""
Geo and geohashing related JSON web service.
To be run behind an nginx server, and supervised by daemontools. That's how I want it to be.
"""

from flup.server.fcgi import WSGIServer
import datetime, time, os, sys
import optparse
import traceback
import simplejson as json
from decimal import Decimal
import random
import hashlib, struct
import web
import urllib

from GraticuleDatabase import GraticuleDatabase
gratsql = "/opt/geo/graticules.sqlite"
gratdb = GraticuleDatabase(gratsql)

try:
  import pgsql as db
except:
  import psycopg2 as db
from DBUtils.PooledDB import PooledDB

CONF = "/opt/geo/geo.conf"
host, dbname, user, password = open(CONF, "r").read().strip().split(",")

pool = PooledDB(db, 3, host=host, database=dbname, user=user, password = '\''+password+'\'')

__usage__ = "%prog -n <num>"
__version__ = "$Id$"
__author__ = "Thomas Hirsch <thomashirsch gmail com>"

FCGI_SOCKET_DIR = '/tmp'
FCGI_SOCKET_UMASK = 0111

TYPE_TEXT  = 0
TYPE_IMAGE = 1
TYPE_LINK  = 2

def geohash(djia, date):
    print djia, date
    sum = hashlib.md5("%s-%s" % (date, djia)).digest()
    lat, lon = [x/2.**64 for x in struct.unpack_from(">QQ", sum)];
    return lat, lon

croxes = ['http://geo.crox.net/djia/%s',
          'http://www1.geo.crox.net/djia/%s',
          'http://www2.geo.crox.net/djia/%s']  
djiacache = {}

def getdjia(date):
    if date in djiacache:
      return djiacache[date]
    
    conn = pool.connection()
    cur  = conn.cursor()

    cur.execute("select djia from djiacache where dato = '%s'" % (date,));
    djia = cur.fetchone()
    if djia:
      return djia[0]

    for crox in croxes:
      try:
        djia = web.get(crox % date)
        if not (("error" in djia) or ("available" in djia)):
          djiacache[date]=djia
          cur.execute("insert into djiacache values ('%s','%s')" % (date, djia))
          conn.commit()
        return djia
      except:
        pass
    try:
      y,m,d = str(date).split("-")
      djia = web.get("http://irc.peeron.com/xkcd/map/data/%s/%s/%s" % (y,m,d))
      return djia
    except Exception,e:
     return None

def reached(title):
    conn = pool.connection()
    cur  = conn.cursor()
    cur.execute("select 1 from categories where title='%s' and category='Coordinates reached'" % (title,))
    if cur.fetchone():
      return True
    return False

def getstats(lat, lon):
    conn = pool.connection()
    cur  = conn.cursor()
    cur.execute("select total, success, d30, d300, last, users from stats where pos = '%s %s'" % (lat, lon))
    data = cur.fetchone()
    return data

def allstats():
    conn = pool.connection()
    cur  = conn.cursor()
    cur.execute("select pos, total, success, d30, d300, cast(last as text), users from stats")
    dico = {}
    for x in cur.fetchall():
      dico[x[0]]=x[1:]
    return json.dumps(dico, use_decimal=True)

def allgrats():
    data = [list(x) for x in gratdb.getAll()]
    dico = {}
    for x in data:
      dico["%s,%s" % (x[0],x[1])]=x[2]
    return json.dumps(dico, use_decimal=True)

def hashlist(lat, lon):
    conn = pool.connection()
    cur  = conn.cursor()
    cur.execute("select title from reports where title like '%% %s %s'" % (lat, lon))
    hashes = []
    for exp in cur.fetchall():
      date, lat, lon = exp[0].split(" ") 
      dico = dict((k,v) for (k,v) in  hashdata(date,lat,lon).items() if k in ["lat","lon","djia"])
      dico['title']=exp[0]
      dico['reached']=reached(exp[0])
      hashes.append(dico)
    return json.dumps(hashes, use_decimal=True)

def participants(lat, lon, date):
    conn = pool.connection()
    cur  = conn.cursor()
    cur.execute("select person from participants where title = '%s %s %s' order by lower(person) asc" % (date, lat, lon))
    people = [x[0] for x in cur.fetchall()]
    return json.dumps(people, use_decimal=True)

def follow(name):
    conn = pool.connection()
    cur  = conn.cursor()
    cur.execute("select title from participants where person = '%s' order by title asc" % (name.replace('\'','\\\'').replace('_',' '),))
    expeditions = [x[0] for x in cur.fetchall()]
    data = []
    for title in expeditions:
      date, lat, lon = title.split(" ")
      dico = dict((k,v) for (k,v) in hashdata(date,lat,lon).items() if k in ["djia","lat","lon"])
      dico['title']=title
      dico['reached']=reached(title)
      data.append(dico)
    return json.dumps(data, use_decimal=True)

def hashdata(sdate, slat, slon):
    result = {}
    date = datetime.datetime.strptime(sdate,"%Y-%m-%d").date()
    latfix = slat =="-0" and "-" or ""
    lonfix = slon =="-0" and "-" or ""
    lat,lon = int(slat), int(slon)

    pdate = str(date - datetime.timedelta(1))
    pdjia = getdjia(pdate)
    if (lon>-30) and (date > datetime.date(2008,5,26)): #only use previous day's coordinates after W30 has been invented.
      date = pdate
      djia = pdjia
      result['w30'] = True
    else:
      ddate = sdate
      djia  = getdjia(ddate)

    if not djia:
      result['error']="Could not retrieve DJIA for %s." % sdate
    elif "not available" in djia:
      result['error']="DJIA for %s not available yet (%s)." % (sdate, djia)
    elif "error" in djia:
      result['error']="service reported an error while retrieving DJIA for %s." % sdate
    else:
      djiacache[date]=djia
      result['djia']= Decimal(djia)

      flat, flon = geohash(djia, sdate)
      glat, glon = geohash(pdjia, sdate) #globalhash always uses previous day's djia

      glat = "%.6f" % (glat * 180 - 90,)
      glon = "%.6f" % (glon * 360 - 180,)

      hlat = "%s%i%s" % (latfix, lat, ("%.6f" % flat)[1:])
      hlon = "%s%i%s" % (lonfix, lon, ("%.6f" % flon)[1:])
      result['lat'] = Decimal(hlat)
      result['lon'] = Decimal(hlon)
      result['global-lat'] = Decimal(glat)
      result['global-lon'] = Decimal(glon)
    return result

def geo(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    result = {}

    cursor=None
    try:
      path = urllib.unquote(environ['REQUEST_URI'])
      parms = path.split("/")
      if len(parms)>2:
        if parms[2]=="stats":
          return allstats() 
        elif parms[2]=="grats":
          return allgrats() 
        elif len(parms)>3 and parms[2]=="follow":
          return follow(parms[3]) 
        elif len(parms)>4 and parms[2]=="list":
          return hashlist(parms[3], parms[4])
        elif len(parms)>5 and parms[2]=="participants":
          return participants(parms[3], parms[4], parms[5])
        elif len(parms)<4:
          return "{'exception':'invalid parameters'}"
      else:
        return "{'exception':'not enough parameters'}"
      latfix = parms[2]=="-0" and "-" or ""
      lonfix = parms[3]=="-0" and "-" or ""
      sdate = None
      if len(parms)>4:
        lat, lon, sdate = int(parms[2]), int(parms[3]), parms[4]
      elif len(parms)==4:
        lat, lon = int(parms[2]), int(parms[3])
      if sdate:
        result = hashdata(sdate, parms[2], parms[3])
      info = gratdb.getLatLon("%s%i" % (latfix, lat), "%s%i" % (lonfix, lon))
      if not info:
        result['graticule'] = None
      else:
        result['graticule'] = info[0] 

      stats = getstats(lat, lon)
      if stats:
        total, success, d30, d300, last, users = stats
        result['attempts']   = total
        result['success'] = success
        result['30d']     = d30
        result['300d']    = d300
        result['last']    = str(last)
        result['hashers'] = users

    except Exception,ex:
      result['exception']=str(ex)
       
    return json.dumps(result, use_decimal=True)

def get_application():
    return geo 

def get_socketpath(name, server_number):
    return os.path.join(FCGI_SOCKET_DIR, 'fcgi-%s-%s.socket' % (name, server_number))

def main(args_in, app_name="geo"):
    p = optparse.OptionParser(description=__doc__, version=__version__)
    p.set_usage(__usage__)
    p.add_option("-v", action="store_true", dest="verbose", help="verbose logging")
    p.add_option("-n", type="int", dest="server_num", help="Server instance number")
    opt, args = p.parse_args(args_in)

    if not opt.server_num:
        print "ERROR: server number not specified"
        p.print_help()

        print "Running test cases."
        #print geo({'REQUEST_URI':'//follow/Felix%20Dance'}, lambda x,y:None)
        #print geo({'REQUEST_URI':'//60/10/2012-03-05'}, lambda x,y:None)
        #print geo({'REQUEST_URI':'//list/60/10'}, lambda x,y:None)
        #print geo({'REQUEST_URI':'//participants/47/10/2009-06-07'}, lambda x,y:None)
        #print geo({'REQUEST_URI':'//follow/Rhonda\'s%20mom'}, lambda x,y:None)
        #print geo({'REQUEST_URI':'//49/9/2009-04-13'}, lambda x,y:None)
        print geo({'REQUEST_URI':'//grats'}, lambda x,y:None)

        return

    socketfile = get_socketpath(app_name, opt.server_num)
    app = get_application()

    try:
        WSGIServer(app,
               bindAddress = socketfile,
               umask = FCGI_SOCKET_UMASK,
               multiplexed = True,
               ).run()
    finally:
        # Clean up server socket file
        os.unlink(socketfile)

if __name__ == '__main__':
    main(sys.argv[1:])
