#!/usr/bin/env python
# -*- coding: utf-8 -*-

import wikipedia, re, string
import math

RE_LINKS = re.compile('(\[\[[Uu]ser *: *(.+?) *(?:\| *(.*?) *)\]\])')

RE_USER = re.compile('\[\[[Uu]ser ?: ?(.+?) ?[\|\]]')
RE_LISTED = re.compile('[\*#]\s*(\[.+?\]|.+?)\s+')
RE_RIBBONBEARER = re.compile('\{\{.*?\|\s*name ?=\s*(.+?)(?:\}|\|\s*\w+\s*=)', re.DOTALL)
RE_CARDRECIPIENT = re.compile('recipient ?=\s*(.+?)(?:\}|\|\s*\w+\s*=)')
RE_ENTITLED = re.compile('==+(\[\[[Uu]ser.*?\])=+=')
RE_MEETUP = re.compile('\{\{\s*[Mm]eet-up.*?\|\s*name\s*=\s*(.+?)(?:\}|\|\s*\w+\s*=)', re.DOTALL)
RE_FIRST = re.compile('^.*?(\[\[[Uu]ser.+?\]\])', re.DOTALL)


improbablenames = ["and", "i", "we", "the", "one"]

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
    if len(p)==0:
      del dic[p]
      continue
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

def identifyParticipants(text, page, getLinks = False):
  global debug_fuzz
  
  #print "===",page,"==="
  fuzzy = {} #user id -> probability of being a participant
  text = unscorify(text)
  
  pseudonyms = {}
  userlinks  = {}
  usernames  = {}

  if "[[Category:Not reached - Did not attempt]]" in text:
    return []

  scoring = {
    RE_USER: 1,
    RE_RIBBONBEARER: 3,
    RE_CARDRECIPIENT: -5,
    RE_ENTITLED: 20,
    RE_MEETUP: 10,
    RE_FIRST: 2,
  }

  sections = getSectionRegex(text, "(participants?|(the )?people|attendees?|adventurers?)\??", True)
  if sections:
    scoring[RE_LISTED] = 5;
    text = sections
  
# identify pseudonyms, and user links
  links = RE_LINKS.findall(text)
  for part in links:
    pseudonyms[part[0].lower()] = part[1].lower()
    userlinks [part[1].lower()] = part[0]
    usernames [part[0].lower()] = part[1]
    if not part[2].lower() in improbablenames:
      pseudonyms[part[2].lower()] = part[1].lower()
      usernames [part[2].lower()] = part[1]
      userlinks [part[2].lower()] = part[0]

  text = text.lower()

  for rex, score in scoring.items():
    match = rex.findall(text)
    for group in match:
      parts = splitgrouped(group)
      for part in parts:
        part = part.lower().strip()
        if not part in improbablenames:
          if part in pseudonyms:
            fuzzy[pseudonyms[part]]=fuzzy.get(pseudonyms[part],0) + score
          else:
            fuzzy[part]=fuzzy.get(part,0) + score
            usernames[part.lower()] = part
  
  #increase the score of a potential participant by the number of mentions¹ vs total mentions 
  mentions = {}
  mcount   = 0.0
  for p in fuzzy.keys():
    mentions[p] = len(re.findall(re.escape(p), text, re.IGNORECASE)) 
    mcount += mentions[p] 
  for p in pseudonyms.keys():
    pseudo_mentions = len(re.findall(re.escape(p), text, re.IGNORECASE)) + len(re.findall(re.escape(p), pseudonyms[p], re.IGNORECASE))
    mentions[pseudonyms[p]] = mentions.get(pseudonyms[p],0) + pseudo_mentions
    mcount += pseudo_mentions

  if mcount>0:
    for p,v in mentions.items():
      fuzzy[p]=fuzzyadd(fuzzy.get(p,0),v/mcount)

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

  fuzzy = normalize(fuzzy)

  participants = []
  for p,v in fuzzy.items():
    if p in improbablenames:
      v = fuzzyadd(v,-1)
    if v>=0.35:
      participants.append(p)

  debug_fuzz = fuzzy
  
  if getLinks:
    return [userlinks.get(p,p) for p in participants] #that is: return a list of [userlinks[p] if it exists, else return p]
  else:
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
