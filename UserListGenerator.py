#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wikipedia, re, string

RE_USER = re.compile('\[\[[Uu]ser ?: ?(.*?) ?[\|\]]')
RE_LISTED = re.compile(' *[\*#] *(.+?)\W')
RE_RIBBONBEARER = re.compile('\{\{.*?name ?= ?(?:\[\[[Uu]ser:)? ?(.*?) ?[\|\}]')
RE_CARDRECIPIENT = re.compile('recipient ?= ?(?:\[\[[Uu]ser:)? ?(.*?) ?[\|\}]')

improbablenames = ["and", "i", "we"]

def fuzzyadd(a,b): #combine two fuzzy values
  return (a+b)/2.0
  #return sqrt(a*a+b*b)

debug_fuzz = None
def getDebugFuzz():
  global debug_fuzz
  return debug_fuzz

def normalize(dic):
  maxfuzz = 0
  for p,v in dic.items():
    if v>maxfuzz:
      maxfuzz=v
  if maxfuzz>0:
    for p,v in dic.items():
      dic[p]=v/maxfuzz
  return dic

def unscorify(word):
  return word.replace("_"," ")

def splitgrouped(word):
  return re.split(",| and |&", word)

def identifyParticipants(text, page):
  global debug_fuzz
  fuzzy = {} #user id -> probability of being a participant
  text = unscorify(text)

  if "[[Category:Not reached - Did not attempt]]" in text:
    return []

  sections = getSectionRegex(text, "(participants?|(the )?people|attendees?|adventurers?)\??", "true")
  if sections:
    linked = RE_USER.findall(sections)
    linkedusers = linked
    for part in linked:
      fuzzy[part]=10.0; 
    #extract non user:-linked users from a list of participants
    listed = RE_LISTED.findall(sections)
    for part in listed:
      if not "[" in part: 
        fuzzy[part]=10.0;
  else:
    linked = RE_USER.findall(text)
    for part in linked:
      fuzzy[part]=fuzzy.get(part,0)+1.0;

  #identify all ribbon bearers
  ribboned = RE_RIBBONBEARER.findall(text)
  for part in ribboned:
    part = splitgrouped(part)
    for ppart in part:
      fuzzy[ppart]=fuzzyadd(fuzzy.get(ppart,1),5);
  #identify all hashcard recipients
  ribboned = RE_CARDRECIPIENT.findall(text)
  for part in ribboned:
    part = splitgrouped(part)
    for ppart in part:
      fuzzy[ppart]=fuzzyadd(fuzzy.get(ppart,1),-5);

  #increase the score of a potential participant by the number of mentions¹ vs total mentions 
  mentions = {}
  mcount   = 0.0
  for p in fuzzy.keys():
    mentions[p] = len(re.findall(re.escape(p), text, re.IGNORECASE))
    mcount += mentions[p] 
  for p in linked: # then subtract one for every linked user (they are "mentioned" twice)
    if p in mentions:
      mentions[p] -= 1
      mcount -= 1
  if mcount>0:
    for p,v in mentions.items():
      fuzzy[p]=fuzzyadd(fuzzy[p],v*v/mcount)

  if len(fuzzy)==0: #only if we still don't have fuzz
    history = page.getVersionHistory(getAll=True)
    #compare the edit history with the page content
    editors = [change[2] for change in history]
    for editor in editors:
      if editor.lower() in text.lower():
        fuzzy[editor]=0.5

  if len(fuzzy)==0: #only if we still don't have fuzz
    wlh = [r for r in page.getReferences()]
    #get user pages from the reference counter
    for l in wlh:
      if "User:" in l.title():
        fuzzy[l.title()[5:]]=0.5
    if len(fuzzy)>1: #but not too much, I say
      fuzzy = {}

  #print fuzzy

  fuzzy = normalize(fuzzy)

  participants = []
  for p,v in fuzzy.items():
    if p in improbablenames:
      v = fuzzyadd(v,-1)
    if v>=0.33:
      participants.append(p)
  

  debug_fuzz = fuzzy
  return participants
  
def getUsers(page):
  """
returns a list of expeditions participants found in the text of a geohashing expedition page.
ingredients: one wikipedia.Page object
  """
  text = page.get()
  title = page.title()
  wikipedia.output(u'Parsing %s...' % title)

  if(text[0] == u"="):  # a hack?
    text = u"\n" + text

  if(text[1] == u"="):
     text = u"\n" + text

#Generate the list of people
#First look in appropriately named "who" sections
  peopleSecText = getSectionRegex(text, "(participants?|people)\??")
  if(peopleSecText != None):
    peopleText = getPeopleText(text, peopleSecText)

#If that fails, look for all unique [[User:*]] tags in the expedition page
  if((peopleSecText == None) or (len(peopleText) == 0)):
    peopleText = getUserList(text)

  return peopleText

def getSections(text, subSects = None):
   text = "\n" + text
   if (subSects == None):
      split_text = re.split("\n", text)
      minlen = 99
      for line in split_text:
         match = re.match("\s*=+", line)
         if ((match != None) and (len(string.strip(match.group(0))) < minlen)):
            minlen = len(string.strip(match.group(0)))
      equal_str = u""  
      for i in range(0,minlen):
         equal_str += u"="
      regex_text = u"\n\s*" + equal_str + "([^=]*?)" + equal_str
   else:
      regex_text = "\n\s*=+([^=]*?)=+"

   text_arr = re.split(regex_text, text)
   for i in range(0,len(text_arr)):
       text_arr[i] = string.strip(text_arr[i])

   section_hash = {}
   section_hash[""] = text_arr[0]

   for i in range(1,len(text_arr),2):
     title = string.lower(text_arr[i])
     section_hash[title] = section_hash.get(title,"") + text_arr[i+1]

#   for i in section_hash.keys():
#      print i + ":",
#      print ":" + section_hash[i]

   return section_hash

def getSection(text, name_arr, subSects = None):
  """
This will look for a section with one of the names in name_arr
The search is case insensitive, and returns the first match, starting from name_arr[0] and continuing to name_arr[len(name_arr)-1]
It will return the body of the appropriate section, or None if there were no matches for the section name.
If subSects != None, then it will search for all subsections which match as well.
  """
  sections = getSections(text, subSects)
  code = ""
  for header in name_arr:
      if header in sections:
          code += sections[header] +"\n"
  if ((len(name_arr) == 0) and ("" in sections)):
      return sections[""]
  if len(code)>0:
    return code
  return None

def getSectionRegex(text, regex_text, subSects = None):
    """
This will look for a section with a name that matches the regex_text
It will return the body of the appropriate section, or None if there were no matches for the section name.
If subSects != None, then it will search for all subsections which match as well.
    """
    sections = getSections(text, subSects)
    if ((regex_text == None) and ("" in sections)):
        return sections[""]
    else:
        for keys in sections.keys():
            if(re.match(regex_text, keys)):
                return sections[keys]
    return None

def getUserUist(text):
  """This will look for all unique user tags on a page, and make a list out of them."""
  regex_res = re.findall("\[\[User:.*?\]\]", text, re.I)
  regex_lower = []
  for i in range(0,len(regex_res)):
    regex_lower.append(re.sub("_", " ", regex_res[i].lower()))
    regex_lower[i] = re.sub(" ?| ?", "|", regex_lower[i])
    regex_lower[i] = re.sub("'s", "", regex_lower[i])
  result_arr = []
  for i in range(0,len(regex_lower)):
    for j in range(i+1,len(regex_lower)):
      if (regex_lower[i] == regex_lower[j]):
        break
      else:
        result_arr.append(regex_res[i])

  temp_str = u", "
  return temp_str.join(result_arr)

def getPeopleText(text, people_text):
  """This function will parse a list of users, and return them in a comma separated list."""
  people_text = re.sub("<!--.*?(-->|$)", "", people_text)
  people_text = string.strip(re.sub("^\[[^][]*?\]", "", people_text))
  people_text_arr = re.split("\n", people_text)

  people_text = u""

  if (len(people_text_arr[0]) == 0):
    people_regex_str = re.compile("^(\[\[.*?\]\]|[^ ]*)")
  elif (people_text_arr[0][0] == "*"):
    people_regex_str = re.compile("^\*\s*(\[\[.*?\]\]|[^ ]*)")
  elif (people_text_arr[0][0] == ":"):
    people_regex_str = re.compile("^:\s*(\[\[.*?\]\]|[^ ]*)")
  else:
    people_regex_str = re.compile("^(\[\[.*?\]\]|[^ ]*)")

  match_obj = people_regex_str.match(people_text_arr[0])
  people_text += match_obj.group(1)

  if(re.match("=", people_text_arr[0])):
    people_text = getUserList(text)
  else:
    for i in range(1,len(people_text_arr)):
      match_obj = people_regex_str.match(people_text_arr[i])
      if ((match_obj != None) and (len(match_obj.group(1)) != 0)):
        if(re.search("Category", people_text_arr[i])):
          pass
        elif (re.match("=", people_text_arr[i])):
          pass
        else:
          people_text += u", "
          people_text += match_obj.group(1)
  return people_text
