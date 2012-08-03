import hashlib, datetime, struct, urllib, re, sys
import time
import wikipedia
import smtplib
from email.mime.text import MIMEText

def send_msg(to_addr, user_msg, lat, lon, centicule, date, username, password):
	print "Send message to",to_addr,"with user msg",user_msg,"about geohash at",lat,lon,"for",date.isoformat(),"because they registered for",centicule,"centicule."

	msg = date.isoformat() + " Notification for the location " + str(lat) + ", " + str(lon) + "\n"
	msg += "These coordinates fall in centicule {:02}\n".format(centicule)
	msg += "Message: " + user_msg + "\n"
	msg += "If this note was sent before 9:30 AM US Eastern time, the coordinates may not be valid."
	print msg

	emailmsg = MIMEText(msg)
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
	notify_file = open(sys.argv[1], 'r')
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
	notify_lat, notify_lon, notify_cent_list, to_addr, notify_msg = re.split('\|', line)

	print "To addr:",to_addr

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
	if str(centicule) in notify_cent_list_arr:
		send_msg(to_addr, notify_msg, lat, lon, centicule, date, username, password)	

notify_file.close()
pass_file.close()
