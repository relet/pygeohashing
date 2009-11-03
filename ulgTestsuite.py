#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, wikipedia, string
from UserListGenerator import *

library = os.listdir("tests")

site = wikipedia.getSite()

failcount = 0
for test in library:
  ftest = open("tests/"+test,"r").read()

  #we expect a comma separated list of participants in the first line
  participants = ftest[:ftest.index("\n")]
  report       = ftest[ftest.index("\n")+1:] #split off the rest
  correct = map(string.lower,map(string.strip,participants.split(",")))

  result = identifyParticipants(report, wikipedia.Page(site, test)) #we might have to connect to the wiki to get the history / what-links-here
  result = map(string.lower, result)  

  for part in correct:
    if not part in result:
      print("OH NOES! We didn't identify %s participating in %s." % (part, test))
      failcount += 1
  for part in result:
    if not part in correct:
      print("OH NOES! We falsely report %s as participating in %s." % (part, test))
      failcount += 1

print("%i tests failed." % failcount)	

  
  