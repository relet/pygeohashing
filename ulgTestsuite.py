#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, wikipedia, string
from UserListGenerator import *

library = os.listdir("tests")

site = wikipedia.getSite()

failcount = 0
total = 0
for test in library:
  ftest = open("tests/"+test,"r").read()

  #we expect a comma separated list of participants in the first line
  participants = ftest[:ftest.index("\n")]
  report       = ftest[ftest.index("\n")+1:] #split off the rest
  correct = [x.lower().strip() for x in participants.split(",") if len(x.strip())>0]

  result = identifyParticipants(report, wikipedia.Page(site, test)) #we might have to connect to the wiki to get the history / what-links-here
  result = map(string.lower, result)  

  failed = False
  for part in correct:
    total += 1
    if not part in result:
      print("OH NOES! We didn't identify %s participating in %s." % (part, test))
      failcount += 1
      failed = True
  for part in result:
    total += 1
    if not part in correct:
      print("OH NOES! We falsely report %s as participating in %s." % (part, test))
      failcount += 1
      failed = True
  if failed:
    print "---\n",getDebugFuzz(),"\n---"

print("%i out of %i tests failed." % (failcount, total))	

  
  