import hashlib, datetime, struct, urllib, re, sys
import time
import wikipedia
import smtplib
from email.mime.text import MIMEText
import codecs

def send_msg(to_addr, user_msg, lat, lon, centicule, date, username, password):
	neglat = "-" if lat < 0 and lat > -1 else ""
	neglon = "-" if lon < 0 and lon > -1 else ""

	print "Send message to",to_addr,"with user msg about geohash at",lat,lon,"for",date.isoformat(),"because they registered for",centicule,"centicule."

	msg = "<html><body><p>"
	msg += date.isoformat() + " Notification for the location " + str(lat) + ", " + str(lon) + "<br></p>"
	msg += "<p>These coordinates fall in centicule {:02}<br></p>".format(centicule)
	msg += '<p><img src="http://carabiner.peeron.com/cgi-bin/static.cgi?date=' + date.isoformat() + '&lat=' + neglat + str(int(lat)) + '&lon=' + neglon + str(int(lon)) + '&zoom=8&width=300&height=400"><br></p>'
	msg += '<p><a href="https://maps.google.com/?ie=UTF8&ll=' + str(lat) + ',' + str(lon) + '&z=9&q=loc:' + str(lat) + ',' + str(lon) + '">Google Maps link</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
	msg += '<a href="http://wiki.xkcd.com/geohashing/' + neglat + str(int(lat)) + ',' + neglon + str(int(lon)) + '">Graticule Page</a>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
	msg += '<a href="http://wiki.xkcd.com/geohashing/' + date.isoformat() + '_' + neglat + str(int(lat)) + '_' + neglon + str(int(lon)) + '">Expedition Page</a><br></p>'
	msg += "<p><br>Message: " + user_msg + "<br></p>"
	msg += "<p>If this note was sent before 9:30 AM US Eastern time, the coordinates may not be valid.</p>"

	for body_charset in 'US-ASCII', 'ISO-8859-1', 'UTF-8':
		try:
        	    msg.encode(body_charset)
	        except UnicodeError:
        	    pass
	        else:
        	    break
	print msg.encode(body_charset)

	emailmsg = MIMEText(msg.encode(body_charset), "html", body_charset)
	emailmsg['Subject'] = "Geohashing notifications."
	emailmsg['To'] = to_addr
	emailmsg['From'] = username

	server = smtplib.SMTP('smtp.gmail.com:587')
	server.starttls()
	server.login(username,password)
	server.sendmail(username,to_addr,emailmsg.as_string())
	server.quit()


def get_fractions(in_lat, in_lon, date):
	if in_lon <= -30:
		w30 = 0
	else:
		w30 = 1
	djia = urllib.urlopen((date - datetime.timedelta(w30)).strftime("http://geo.crox.net/djia/%Y/%m/%d")).read()
	if '404 Not Found' in djia: return [0, 0]
	if 'data not available yet' in djia: return [0, 0]
	sum = hashlib.md5("%s-%s" % (date, djia)).digest()
	lat, lon = [x/2.**64 for x in struct.unpack_from(">QQ", sum)]
	return [lat, lon]

non_lat_frac = 0
while non_lat_frac == 0:
	non_lat_frac, non_lon_frac = get_fractions(0, -80, datetime.date.today())
	if non_lat_frac == 0:
		print "Waiting for DJIA data"
		time.sleep(60)

w_lat_frac, w_lon_frac = get_fractions(0, 0, datetime.date.today() + datetime.timedelta(1))

if len(sys.argv) > 1:
	notify_file = codecs.open(sys.argv[1], mode='r', encoding='utf-8')
else:
	print "ERROR: Need notification file"
	sys.exit(1)

if len(sys.argv) > 2:
	pass_file = open(sys.argv[2], 'r')
else:
	print "ERROR: Need password file"
	notify_file.close()
	sys.exit(1)

try:
	username = pass_file.readline().strip()
	password = pass_file.readline().strip()
except:
	print "Badly formatted pass file"
	sys.exit(1)


enwiktsite = wikipedia.getSite('en', 'geohashing')

for line in notify_file:
	to_addr, wiki_page = re.split('\|', line)

	print "To addr:",to_addr
#	print "Wiki page:",wiki_page

	user_page = wikipedia.Page(enwiktsite, wiki_page)
	user_page_text = user_page.get()

	#print "Wiki page text:",user_page_text
	# print re.split('\|-', user_page_text)
	for notify_line in re.split('\|-', user_page_text):
		if '{' in notify_line:
			continue
		if '}' in notify_line:
			continue
		if '!' in notify_line:
			continue
		notify_line_arr = re.split('\s*\|+\s*',notify_line.strip())
		if len(notify_line_arr[0]) == 0:
			notify_lat = notify_line_arr[1]
			notify_lon = notify_line_arr[2]
			notify_cent_list = notify_line_arr[3]
			notify_msg = notify_line_arr[4]
		else:
			notify_lat = notify_line_arr[0]
			notify_lon = notify_line_arr[1]
			notify_cent_list = notify_line_arr[2]
			notify_msg = notify_line_arr[3]

		if float(notify_lon) <= -30:
			lon = float(notify_lon) - non_lon_frac
			if float(notify_lat) < 0 or notify_lat == "-0":
				lat = float(notify_lat) - non_lat_frac
			else:
				lat = float(notify_lat) + non_lat_frac
			date = datetime.date.today()
		else:
			if float(notify_lon) < 0 or notify_lon == "-0":
				lon = float(notify_lon) - w_lon_frac
			else:
				lon = float(notify_lon) + w_lon_frac
			if float(notify_lat) < 0 or notify_lat == "-0":
				lat = float(notify_lat) - w_lat_frac
			else:
				lat = float(notify_lat) + w_lat_frac
			date = datetime.date.today() + datetime.timedelta(1)
		
		dec_lat = int(abs(lat - int(lat)) * 10)
		dec_lon = int(abs(lon - int(lon)) * 10)
		centicule = dec_lat * 10 + dec_lon
		notify_cent_list_arr = re.split('\s+', notify_cent_list)
		if '*' in notify_cent_list_arr:
			send_msg(to_addr, notify_msg, lat, lon, centicule, date, username, password)	
		if str(centicule).zfill(2) in notify_cent_list_arr:
			send_msg(to_addr, notify_msg, lat, lon, centicule, date, username, password)	

notify_file.close()
pass_file.close()
