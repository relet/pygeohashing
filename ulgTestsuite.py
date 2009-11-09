#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, wikipedia, string
from UserListGenerator import *
import re

library = os.listdir("tests")

site = wikipedia.getSite()

RE_LINKS = re.compile("\s*((?:\[\[.+?\]\])|(?:[^,[]+))\s*,?")

failcount = 0
total = 0
for test in library:
  ftest = open("tests/"+test,"r").read()

  #we expect a comma separated list of participants in the first line
  #we expect a comma separated list of participants in links form in the second line
  participants = ftest[:ftest.index("\n")]
  rest         = ftest[ftest.index("\n")+1:] #split off the rest
  links        = rest [:rest.index("\n")]
  report       = rest [rest.index("\n")+1:] #split off the rest
  correct_parts = [x.lower().strip() for x in participants.split(",") if len(x.strip())>0]
  correct_links = [x.strip() for x in RE_LINKS.findall(links) if len(x.strip())>0]
  result_parts = identifyParticipants(report, wikipedia.Page(site, test), None) #we might have to connect to the wiki to get the history / what-links-here
  result_parts = map(string.lower, result_parts)  

  parts_debug = getDebugFuzz()

  links_debug = {}
  links_debug_links = {}

  any_failed = False

  failed = False
  for part in correct_parts:
    total += 1
    if not part in result_parts:
      reason = "(Identification fail)"
      if part.lower() in parts_debug.keys():
        reason = "(Wrong rating)"
      print("OH NOES! We didn't identify %s participating in %s for names test. %s" % (part, test, reason))      
      failcount += 1
      failed = True
  for part in result_parts:
    total += 1
    if not part in correct_parts:
      print("OH NOES! We falsely report %s as participating in %s for names test." % (part, test))
      failcount += 1
      failed = True
  if failed:
    any_failed = True

  result_links = identifyParticipants(report, wikipedia.Page(site, test), True) #we might have to connect to the wiki to get the history / what-links-here
  #We want caps-specific results for links

  failed = False
  for part in correct_links:
    total += 1
    if not part in result_links:
      print("OH NOES! We didn't identify %s participating in %s for links test." % (part, test))
      failcount += 1
      failed = True
  for part in result_links:
    total += 1
    if not part in correct_links:
      print("OH NOES! We falsely report %s as participating in %s for links test." % (part, test))
      failcount += 1
      failed = True
  if failed:
    any_failed = True
    links_debug = getDebugFuzz()
    links_debug_links = getDebugLinks()

  if any_failed:
    print "\n---\n",parts_debug,"\n",links_debug,"\n",links_debug_links,"\n---"

print("%i out of %i tests failed." % (failcount, total))	

  
  
