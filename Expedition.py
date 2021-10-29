
import pywikibot
import re, datetime
from UserListGenerator import *

date_comment = u'<!--DATE-->'
gratadd_comment = u'<!--GRATADD-->'
gratname_comment = u'<!--GRATNAME-->'
people_count_comment = u'<!--PEOP_COUNT-->'
people_comment = u'<!--PEOPLE-->'
location_comment = u'<!--LOCATION-->'
transport_icon_comment = u'<!--TRANSICON-->'
transport_comment = u'<!--TRANSPORT-->'
reached_comment = u'<!--REACHED-->'
reason_comment = u'<!--REASON-->'
link_comment = u'<!--LINK-->'
exped_comment = u'<!--EXPED-->'
usertext_comment = u'<!--USERTEXT-->'
reached_icon_comment = u'<!--REACHICON-->'

RE_DATE = re.compile('DATE')
RE_GRATADD = re.compile('GRATADD')
RE_GRATNAME = re.compile('GRATNAME')
RE_PEOPLE_COUNT = re.compile('PEOPLE:(\d+)')
RE_PEOPLE = re.compile('PEOPLE')
RE_LOCATION = re.compile('LOCATION')
RE_TRANSPORT_ICON = re.compile('TRANSICON')
RE_TRANSPORT = re.compile('TRANSPORT')
RE_REACHED = re.compile('REACHED:(.*?):(.*?):REACHED')
RE_REACHED_ICON = re.compile('REACHICON')
RE_REASON = re.compile('REASON')
RE_LINK = re.compile('LINK')
RE_EXPED = re.compile('EXPED')
RE_USERTEXT = re.compile('USERTEXT')
RE_REACHED2 = re.compile('REACHED.*?REACHED')
RE_PEOPLE_COUNT2 = re.compile('PEOPLE.:(\d+)')
RE_LISTLEN = re.compile('LISTLEN:(-?\d+)')
RE_LISTLEN2 = re.compile('LISTLEN:(.-)?\d+')

RE_APECOMMENT = re.compile("\<\!\-\-APE (.*?)\-\-\>")

RE_HTMLCOMMENT = re.compile("\<\!\-\-.*?\-\-\>+", re.DOTALL)
RE_HTMLCOMMENT_BEGIN = re.compile("\<\!\-\-.*$", re.DOTALL)
RE_HTMLCOMMENT_END = re.compile("^.*\-\-\>", re.DOTALL)
RE_TEMPLATE_NEST = re.compile("\{\{[^}]*?\{\{.*?\}+.*?\}+", re.DOTALL)
RE_TEMPLATE = re.compile("\{+.*?\}+", re.DOTALL)
RE_IMAGE = re.compile("\[\[Image:.*?\]\]", re.DOTALL)
RE_CATEGORY = re.compile("\[\[Category:.*?\]\]", re.DOTALL)
RE_HTMLTAG = re.compile("\<+.*?\>+", re.DOTALL)
RE_SECTIONHEADER = re.compile("=+.*?=+", re.DOTALL)
RE_BULLETS = re.compile("^[*:]+", re.DOTALL)
RE_THISHASHPOINT = re.compile("^(The|This|Today's)\s+?(location|hash ?point|geo ?hash)\s+?(is)?", re.IGNORECASE)
RE_NOTOC = re.compile("__NOTOC__", re.DOTALL)
RE_BIKE = re.compile("((bike)|(bicycle))", re.IGNORECASE)
RE_BUS = re.compile("bus", re.IGNORECASE)
RE_TRAIN = re.compile("train", re.IGNORECASE)
RE_WALK = re.compile("walk(ed)?", re.IGNORECASE)
RE_STRIPCAT = re.compile("Category:")
RE_CATNOTREACH = re.compile("Category:Not reached - ")

class Expedition:
  '''
  This contains all important information about a given expedition
  '''
  def __init__(self, site, pageName, db, format = None):
    self.pageName = pageName
    self.page = pywikibot.Page(site, self.pageName)
    pageNameParts = re.split("[ _]+", self.pageName)
    self.date = pageNameParts[0]
    graticule = pageNameParts[1:3] # either ["global"] or ["lat", "lon"]
    self.gratAdd = u" ".join(graticule)
    self.gratAddr = u",".join(graticule)
    isGlobalhash = pageNameParts[1] == "global"
    
    if isGlobalhash:
      self.lat = None
      self.lon = None
    else:
      self.lat = pageNameParts[1]
      self.lon = pageNameParts[2]
    
    name_list = db.getLatLon(self.lat,self.lon)
    if((name_list == None) or (name_list[1] == None) or (name_list[2] == None)):
      if isGlobalhash:
        self.gratName = u"Globalhash"
      else:
        self.gratName = u"Unknown (" + self.lat + u", " + self.lon + u")"
    else:
      self.gratName = name_list[1] + u", " + name_list[2]
    if self.page.isRedirectPage():
      self.text = u""
      self.people = None
      self.categories = []
    else:
      self.text = self.page.get()
      self.people = identifyParticipants(self.text, self.page, getLinks = True)
      self.categories = self.page.categories()

    if self.people:
      self.peopleText = ", ".join(self.people)
    else:
      if(datetime.date.today().isoformat() <= self.date):
        self.peopleText = u"Someone is, why not join them?"
      else:
        self.peopleText = u"Someone went"
    self.location = self._getLocationText(self.text)
    (self.transport, self.transportIcons) = self._getTransportText(self.text)
    self.reached = False

    reasons = []
    for cat in self.categories:
      if ("Category:Coordinates reached" == cat.title()):
        self.reached = True

      if (RE_CATNOTREACH.search(cat.title()) != None):
        reasons.append(RE_CATNOTREACH.sub("", cat.title()))

    self.failReason = ", ".join(reasons)

    if format:
      self.format = format
    else:
      self.format = u" date DATE - gratadd GRATADD - gratname GRATNAME - people PEOPLE - location LOCATION - transport TRANSPORT - reached REACHED:Succeeded:Failed:REACHED - reason REASON - link LINK - exped EXPED - usertext USERTEXT"
      self.format = u"|-\n|DATE||GRATADD||GRATNAME||PEOPLE||REACHED:[[EXPED|Succeeded]]:[[EXPED|Failed]]:REACHED||LOCATION"

  def _getTransportText(self, fullText):
    transportList = []
    transportIconList = []
    regexArr = [
      (RE_BIKE, "Bicycle", "[[Image:Bikegeohash.png|22px]]"),
      (RE_BUS, "Bus", "[[Image:Bus.PNG|24px]]"),
      (RE_TRAIN, "Train", "[[Image:Bus.PNG|24px]]"),
      (RE_WALK, "Walk", "[[Image:Walk.PNG|24px]]")
    ]
    for rex,text,icon in regexArr:
      if (rex.search(fullText) != None):
        transportList.append(text) 
        transportIconList.append(icon)
    return (", ".join(transportList), "".join(transportIconList))

  def getDate(self):
    return self.date

  def getPagename(self):
    return self.pageName

  def getExpeditionSummary(self):
    link = u"[[" + self.pageName + u"|" + self.gratName + u"]]"
    expSum = link + u" || " + self.peopleText + u" || " + self.location
    return expSum

  def _getLocationText(self, text):
    '''
    Generate the Location text
    '''
#First look in appropriately named "where" sections
    locationSecText = getSectionRegex(text, "(location|where|about|the spot)\??")

#If that fails, look in appropriately named "expedition" sections
    if ((locationSecText == None) or (len(self._getLocationTrimmed(locationSecText)) == 0)):
        locationSecText = getSectionRegex(text, "expeditions?")

#If that fails, look before any section headers
    if ((locationSecText == None) or (len(self._getLocationTrimmed(locationSecText)) == 0)):
        locationSecText = getSectionRegex(text, None)

    if(locationSecText != None):
        locationText = self._getLocationTrimmed(locationSecText)
    else:
        locationText = ""

    if(locationText == ""):
      if(datetime.date.today().isoformat() <= self.date):
        locationText = u"Description unavailable, why not have a spontaneous adventure?"
      else:
        locationText = u"Somewhere"
    return locationText
      
  def _getLocationTrimmed(self, locationSecText):
    locationText = u" ".join(re.split("\n", locationSecText))
    regexArr = [ RE_HTMLCOMMENT, RE_HTMLCOMMENT_BEGIN, RE_HTMLCOMMENT_END,
      RE_TEMPLATE_NEST, RE_TEMPLATE, RE_IMAGE, RE_CATEGORY, RE_HTMLTAG,
      RE_SECTIONHEADER, RE_BULLETS, RE_THISHASHPOINT, RE_NOTOC
    ]

    for rex in regexArr:
      locationText = rex.sub("", locationText).strip()

    resText = u""
    resTextLen = 0
    iterLen = 1
#This is to allow for links in the location text.
#Only full links should be included.
    while((resTextLen < 75) and (len(locationText) > 0) and (iterLen != resTextLen)):
        iterLen = resTextLen
        matchObj = re.match("^([^[]*?)(http:|\[|$)", locationText)
        if(matchObj != None):
            locationText = locationText[len(matchObj.group(1)):len(locationText)]
        if((matchObj != None) and (len(matchObj.group(1)) != 0)):
            resText += matchObj.group(1)[0:min(len(matchObj.group(1)),75-resTextLen)]
            resTextLen += min(len(matchObj.group(1)),75-resTextLen)

        if(resTextLen < 75):
            matchObj = re.match("^(\[+[^\]]*\]+|http:\S*)", locationText)
            locationText = re.sub("^(\[+[^\]]*\]+|http:\S*)", "", locationText)
            if((matchObj != None) and (len(matchObj.group(0)) != 0)):
                resText += matchObj.group(0)
                resTextLen += self._getLinkLength(matchObj.group(0))
    if(resTextLen >= 75):
        resText += u"..."
    return resText

#This should tell us how long a link will appear when it is replaced by text.
  def _getLinkLength(self, linkText):
    actLength = len(linkText)
    if(linkText[0] != "["):
      return actLength
    if((actLength > 1) and (linkText[1] != "[")):
      matchObj = re.match("^[^ ]* ([^\]]+)\]", linkText)
      if((matchObj != None) and (len(matchObj.group(1)) != 0)):
        return len(matchObj.group(1))
      else:
        return 0
    else:
      matchObj = re.match("^[^|]*\|([^\]]+)\]\]", linkText)
      if((matchObj != None) and (len(matchObj.group(1)) != 0)):
        return len(matchObj.group(1))
      else:
        return 0


  def people_count_func(self, matchObj):
    return people_count_comment + ", ".join(self.people_temp[0:int(matchObj.group(1))]) + people_count_comment

  def subFormat(self, format = None, user = None, oldText = None, grat = None):
    if grat:
        grat_addr = self.gratAddr
        if grat_addr != grat:
            return None
    userFound = False
    if (oldText == None):
      userComment = u''
    else:
      userComment = re.sub(".*" + usertext_comment + "(.*)" + usertext_comment + ".*", u'\\1', oldText)
    if self.reached:
      reached = u'\\1'
      reached_icon = u'[[Image:Arrow2.png|12px]]'
    else:
      reached = u'\\2'
      reached_icon = u'[[Image:Arrow4.png|12px]]'

    people = []
    if self.people:
      if user:
        for person in self.people:
          if(re.search(u"User:\s*" + user + u"[|\]]", person, re.IGNORECASE) == None):
            people.append(person)
          else:
            userFound = True
      else:
        people = self.people
    if ((user != None) and (userFound != True)):
      return None
    if (len(people) == 0):
      people = [u""]
    
    self.people_temp = people
    formats = [
      (RE_REACHED_ICON,   reached_icon_comment   + reached_icon            + reached_icon_comment),
      (RE_REACHED,        reached_comment        + reached                 + reached_comment),
      (RE_DATE,           date_comment           + self.date               + date_comment),
      (RE_GRATADD,        gratadd_comment        + self.gratAdd            + gratadd_comment),
      (RE_GRATNAME,       gratname_comment       + self.gratName           + gratname_comment),
      (RE_PEOPLE_COUNT,   self.people_count_func),
      (RE_PEOPLE,         people_comment         + ", ".join(people)       + people_comment),
      (RE_LOCATION,       location_comment       + self.location           + location_comment),
      (RE_TRANSPORT_ICON, transport_icon_comment + self.transportIcons     + transport_icon_comment),
      (RE_TRANSPORT,      transport_comment      + self.transport          + transport_comment),
      (RE_REASON,         reason_comment         + self.failReason         + reason_comment),
      (RE_LINK,           link_comment           + "[["+self.pageName+"]]" + link_comment),
      (RE_EXPED,          exped_comment          + self.pageName           + exped_comment),
      (RE_USERTEXT,       usertext_comment       + userComment             + usertext_comment),
      (RE_LISTLEN,        ""),
    ]
    formatted_out = u"<!--APE " + self.date + u" " + self.gratAdd + u"-->";
    if format:
      formatted_out += format
    else:
      formatted_out += self.format
    for rex, sub in formats:
      formatted_out = rex.sub(sub, formatted_out)
    self.people_temp = None
    return formatted_out
