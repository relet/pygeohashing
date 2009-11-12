
import re, wikipedia, datetime
from UserListGenerator import *

RE_DATE = re.compile('DATE');
RE_GRATADD = re.compile('GRATADD');
RE_GRATNAME = re.compile('GRATNAME');
RE_PEOPLE = re.compile('PEOPLE');
RE_LOCATION = re.compile('LOCATION');
RE_TRANSPORT = re.compile('TRANSPORT');
RE_REACHED = re.compile('REACHED');
RE_REASON = re.compile('REASON');
RE_LINK = re.compile('LINK');

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
RE_STRIPCAT = re.compile("Category:")
RE_CATNOTREACH = re.compile("Category:Not reached - ")

class Expedition:
  '''
  This contains all important information about a given expedition
  '''
  def __init__(self, site, pageName, db, formats = None):
    self.pageName = pageName
    self.page = wikipedia.Page(site, self.pageName)
    pageNameParts = re.split("[ _]+", self.pageName)
    self.date = pageNameParts[0]
    self.lat = pageNameParts[1]
    self.lon = pageNameParts[2]
    self.gratAdd = self.lat+" "+self.lon
    name_list = db.getLatLon(self.lat,self.lon)
    if((name_list == None) or (name_list[1] == None) or (name_list[2] == None)):
      self.gratName = u"Unknown (" + self.lat + u", " + self.lon + u")"
    else:
      self.gratName = name_list[1] + u", " + name_list[2]
    self.text = self.page.get()

    self.people = identifyParticipants(self.text, self.page, getLinks = True)
    if self.people:
      self.peopleText = ", ".join(self.people)
    else:
      if(datetime.date.today().isoformat() <= self.date):
        self.peopleText = u"Someone is, why not join them?"
      else:
        self.peopleText = u"Someone went"
    self.location = self._getLocationText(self.text)
    self.transport = self._getTransportText(self.text)
    self.reached = False

    self.categories = self.page.categories()
    reasons = []
    for cat in self.categories:
      if ("Category:Coordinates reached" == cat.title()):
        self.reached = True

      if (RE_CATNOTREACH.search(cat.title()) != None):
        reasons.append(RE_CATNOTREACH.sub("", cat.title()))

    self.failReason = ", ".join(reasons)

    if formats:
      self.formats = formats
    else:
      self.formats = {}
      self.formats[""] = "DATE - GRATADD - GRATNAME - PEOPLE - LOCATION - TRANSPORT - REACHED - REASON - LINK\n"

  def _getTransportText(self, fullText):
    transportList = []
    regexArr = [
      (RE_BIKE, "Bicycle"),
      (RE_BUS, "Bus"),
      (RE_TRAIN, "Train")
    ]
    for rex,text in regexArr:
      if (rex.search(fullText) != None):
        transportList.append(text) 
    return ", ".join(transportList)

  def getDate(self):
    return self.date

  def getExpeditionSummary(self):
    link = u"[[" + self.pageName + u"|" + self.gratName + u"]]"
    expSum = link + u" - " + self.peopleText + u" - " + self.location
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



  def subFormat(self):
    formats = [
      (RE_DATE,      "[["+self.date+"]]"),
      (RE_GRATADD,   self.gratAdd),
      (RE_GRATNAME,  "[["+self.gratName+"]]"),
      (RE_PEOPLE,    ", ".join(self.people)),
      (RE_LOCATION,  self.location),
      (RE_TRANSPORT, self.transport),
      (RE_REACHED,   self.reached),
      (RE_REASON,    self.failReason)
      (RE_LINK,   "[["+self.pageName+"]]"),
    ]
    formatted_out = self.format
    for rex, sub in formats:
      formatted_out = rex.sub(sub, formatted_out)
    return fomatted_out

