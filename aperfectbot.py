import sys
sys.path

import pywikibot
import re, string
import GraticuleDatabase
from pywikibot import Category
import sys, datetime
import hashlib, struct, urllib
import time
from UserListGenerator import *
import Expedition, ExpeditionSummaries
import os
import copy
import traceback
import codecs

#ccodes  = {}
#for line in open("countryCodes.txt","r"):
#  data = line.split("\t")
#  ccodes[data[1]]=data[0]

# site = wikipedia.getSite()

RE_EXPLIST_COMMENT = re.compile('\<\!\-\-EXPLIST\-\-\>(.*)\<\!\-\-EXPLIST\-\-\>', re.DOTALL)

# You must pass a date after the last available one
def get_last_day_avail(date):
    #djia = urllib.urlopen((date - datetime.timedelta(1)).strftime("http://carabiner.peeron.com/xkcd/map/data/%Y/%m/%d")).read()
    djia = urllib.urlopen((date - datetime.timedelta(1)).strftime("http://geo.crox.net/djia/%Y/%m/%d")).read()
    if djia.find('404 Not Found') >= 0:
        date = get_last_day_avail(date - datetime.timedelta(1))
    return date

#Split the page title up on spaces/underscores
def get_page_title_sections(title):
    return re.split("[ _]+", title)

#Look for the failsafe stop
def check_banana(site):
    check_page = pywikibot.Page(site, "User:AperfectBot")
    check_text = check_page.get(True)
    check_arr = re.split("\n", check_text)
    check_text = u" ".join(check_arr)
    check_regex = re.search("==Distraction Banana==\s*(.*?)\s*$", check_text, re.S)
    if(len(check_regex.group(1)) == 0):
        return 0
    else:
        return 1

#A macro for writing pages out    
def page_write(page, text, site):
    try:
      old_text = page.get()
    except:
      page.put(text, u"Ook.")
    else:
      if (text == old_text):
        print "Page",page.title(),"has not changed, skipping"
      else:
        page.put(text, u"Ook.")

#Write a date page if it doesn't already exist.
def date_page_write(date, site):
    page_text = u"<noinclude>{{date navigation}}</noinclude>\n"
    page_text += u"{{auto coordinates|" + date + "}}\n"
    page_text += u"{{auto gallery2|" + date + "}}\n"
    page_text += u"<noinclude>{{expedition summaries|" + date + "}}</noinclude>\n"

    page = pywikibot.Page(site, date)
    if(not page.exists()):
        page = pywikibot.Page(site, date)
        page_write(page, page_text, site)
        add_date(site, date)

#For displaying dates in a different manner than normal
def holiday_lookup(date):
    return date

expedListPeople = {}
expedListGrats = {}

#Get up to 3 update requests from the page
def get_old_dates(site, db):
    global expedListPeople
    global expedListGrats

    page = pywikibot.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()

    matches = re.findall("(''')?(\d{4}-\d{2}-\d{2})(''')?", all_text)

    all_text = re.sub("(''')?(\d{4}-\d{2}-\d{2})(''')?", "'''\g<2>'''", all_text, 3)

    match_list = []
    for i in range(0, min(len(matches), 3)):
        match_list.append(matches[i][1])

    page = pywikibot.Page(site, u"User:AperfectBot/Update_requests")
    page_write(page, all_text, site)

    fh = open("aperfectbot_updates.txt", "r")
    all_text = fh.read()

    matches = re.findall("(''')?(\d{4}-\d{2}-\d{2})(''')?", all_text)
    all_text = re.sub("(''')?(\d{4}-\d{2}-\d{2})(''')?", "'''\g<2>'''", all_text, 3)
    match_list2 = []
    for i in range(0, min(len(matches), 3)):
        match_list.append(matches[i][1])
    fh.close()

    for date in match_list:
        expedSum = ExpeditionSummaries.ExpeditionSummaries(site, date, db)
        expedListPeople = updateExpedLists(expedSum, expedListPeople, date)
        expedListGrats = updateExpedListsGrats(expedSum, expedListGrats, date)

    remove_dates(site, match_list)

    return match_list

#Clear off the dates which were just updated
def remove_dates(site, dates):
    page = pywikibot.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()    

    fh = open("aperfectbot_updates.txt", "r")
    all_text_file = fh.read()
    fh.close()

    for i in dates:
        all_text = re.sub("(''')?" + i + "(''')?\n*", "", all_text)
        all_text_file = re.sub("(''')?" + i + "(''')?\n*", "", all_text_file)
        all_text_file += "\n" + i

    page = pywikibot.Page(site, u"User:AperfectBot/Update_requests")
    page_write(page, all_text, site)

    fh = open("aperfectbot_updates.txt", "w")
    fh.write(all_text_file)
    fh.close()


def add_date(site, date):
    page = pywikibot.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()    
    all_text += "\n\n" + date
    page = pywikibot.Page(site, u"User:AperfectBot/Update_requests")
    page_write(page, all_text, site)


def getExpeditionSummaries(expPages, db, dates, firstDate):
    allSummaries = {}
    if dates:
        for date in dates:
            allSummaries[date] = []
    for page in expPages:
        if(re.match("\d{4}-\d{2}-\d{2} [-0-9]{1,4} [-0-9]{1,4}$", page.title())):
            pageNameParts = re.split("[ _]+", page.title())
            if (firstDate == None) or (pageNameParts[0] >= firstDate):
                print "Parsing page",expPages.index(page),"of",len(expPages),":",page.title()
                exped = Expedition.Expedition(page.site(), page.title(), db)
                if not exped.getDate() in allSummaries:
                    allSummaries[exped.getDate()] = []

                allSummaries[exped.getDate()].append(exped.getExpeditionSummary())
    return allSummaries

def putExpeditionSummaries(summaries, site):
    date_keys = summaries.keys()
    date_keys.sort()
    date_keys.reverse()
    for i in date_keys:
        all_text = u"<noinclude>This page is automatically generated.  Any edits to this page will be overwritten by a bot.\n\n</noinclude>\n|-\n|"
        all_text += u"\n|-\n|".join(summaries[i])
        page = pywikibot.Page(site, "Template:Expedition_summaries/" + i)
        page_write(page, all_text, site)
        #Only update the date page if its in the future, and its 9:** AM
        # if(datetime.date.today().isoformat() <= i):
        date_page_write(i, site)

#Get the list of people who have requested expedition lists
def getPersonList(site):
    page = pywikibot.Page(site, u"User:AperfectBot/User_expedition_lists")
    people_hash = getSections(page.get())
    return people_hash

#Get the list of people who have requested expedition lists
def getGratList(site):
    page = pywikibot.Page(site, u"User:AperfectBot/Grat_expedition_lists")
    grat_hash = getSections(page.get())
    return grat_hash
    
#Get all of the expeditions already parsed for a specific user.
def getExpeditions(site, person, person_entry):
    formats = [
      (Expedition.RE_DATE,           re.escape(Expedition.date_comment)            + ".*?" + re.escape(Expedition.date_comment)),
      (Expedition.RE_GRATADD,        re.escape(Expedition.gratadd_comment)         + ".*?" + re.escape(Expedition.gratadd_comment)),
      (Expedition.RE_GRATNAME,       re.escape(Expedition.gratname_comment)        + ".*?" + re.escape(Expedition.gratname_comment)),
      (Expedition.RE_PEOPLE_COUNT2,  re.escape(Expedition.people_count_comment)    + ".*?" + re.escape(Expedition.people_count_comment)),
      (Expedition.RE_PEOPLE,         re.escape(Expedition.people_comment)          + ".*?" + re.escape(Expedition.people_comment)),
      (Expedition.RE_LOCATION,       re.escape(Expedition.location_comment)        + ".*?" + re.escape(Expedition.location_comment)),
      (Expedition.RE_TRANSPORT_ICON, re.escape(Expedition.transport_icon_comment)  + ".*?" + re.escape(Expedition.transport_icon_comment)),
      (Expedition.RE_TRANSPORT,      re.escape(Expedition.transport_comment)       + ".*?" + re.escape(Expedition.transport_comment)),
      (Expedition.RE_REACHED_ICON,   re.escape(Expedition.reached_icon_comment)    + ".*?" + re.escape(Expedition.reached_icon_comment)),
      (Expedition.RE_REACHED2,       re.escape(Expedition.reached_comment)         + ".*?" + re.escape(Expedition.reached_comment)),
      (Expedition.RE_REASON,         re.escape(Expedition.reason_comment)          + ".*?" + re.escape(Expedition.reason_comment)),
      (Expedition.RE_LINK,           re.escape(Expedition.link_comment)            + ".*?" + re.escape(Expedition.link_comment)),
      (Expedition.RE_EXPED,          re.escape(Expedition.exped_comment)           + ".*?" + re.escape(Expedition.exped_comment)),
      (Expedition.RE_USERTEXT,       re.escape(Expedition.usertext_comment)        + ".*?" + re.escape(Expedition.usertext_comment)),
      (Expedition.RE_LISTLEN2,       ""),
    ]

    text_arr = re.split('\n', person_entry)
#    print "Fetching ", text_arr[0]
    page = pywikibot.Page(site, text_arr[0])
    if(page.exists()):
      page_text = page.get()
    else:
      page_text = u""        

    exp_list_text_match = RE_EXPLIST_COMMENT.search(page_text)
    if(exp_list_text_match != None):
      exp_list_text = exp_list_text_match.group(1)
    else:
      exp_list_text = u""

    formatText = u"(" + Expedition.RE_APECOMMENT.pattern + re.escape("\n".join(text_arr[1:])) + u")"

    for rex, repl in formats:
      formatText = rex.sub(repl, formatText)

    page_matches = re.findall(formatText, exp_list_text)

    customExpedList = {}

    for text, name in page_matches:
      customExpedList[name] = text

    return [u"\n".join(text_arr[1:]), customExpedList, text_arr[0]]
    
#Get all the current per-user expedition lists
def parseExpedLists(site):
    people_hash = getPersonList(site)
    localExpedListPeople = {}

    for person in people_hash.keys():
      if(len(person) != 0):
        localExpedListPeople[person] = getExpeditions(site, person, people_hash[person])
    return localExpedListPeople

#Get all the current per-graticule expedition lists
def parseExpedListsGrats(site):
    grat_hash = getGratList(site)
    localExpedListGrats = {}

    for grat in grat_hash.keys():
      if(len(grat) != 0):
        localExpedListGrats[grat] = getExpeditions(site, grat, grat_hash[grat])
    return localExpedListGrats

#Update the expedition lists with new data found this run
def updateExpedLists(expedSums, expedListPeople, date):
    for person in expedListPeople.keys():
      if(len(person) > 0):
	for exped_name in expedListPeople[person][1].keys():
          if date in exped_name:
            #print "Removing",exped_name,"from",person
            del expedListPeople[person][1][exped_name]
        expedListPeople[person][1].update(expedSums.getSubFormats(format = expedListPeople[person][0], user = person, oldText = expedListPeople[person][1]))
    return expedListPeople

def updateExpedListsGrats(expedSums, expedListGrats, date):
    print "Operating on",date
    for grat in expedListGrats.keys():
      if(len(grat) > 0):
	for exped_name in expedListGrats[grat][1].keys():
          if date in exped_name:
            #print "Removing",exped_name,"from",grat
            del expedListGrats[grat][1][exped_name]
        expedListGrats[grat][1].update(expedSums.getSubFormats(format = expedListGrats[grat][0], grat = grat, oldText = expedListGrats[grat][1]))
    return expedListGrats


#Update the USERTEXT sections of the expedition list and write out the whole list
def updateUserTexts(site):
    global expedListPeople
    re_text = Expedition.RE_USERTEXT.pattern + ".*?" + Expedition.RE_USERTEXT.pattern
    RE_USERTEXT_COMMENT = re.compile(re_text, re.DOTALL)
    people_hash = getPersonList(site)
    for person in people_hash.keys():
      if(len(person) > 0):
        if (expedListPeople[person] == expedListPeopleOrig[person]):
          print "Page", expedListPeople[person][2], "has not changed, skipping"
          continue
          
        personExpeds = getExpeditions(site, person, people_hash[person])
        for date in personExpeds[1].keys():
          matchObj = RE_USERTEXT_COMMENT.search(personExpeds[1][date])
          if ((matchObj != None) and (date in expedListPeople[person][1].keys())):
            expedListPeople[person][1][date] = RE_USERTEXT_COMMENT.sub(matchObj.group(0),expedListPeople[person][1][date])
        writeExpedListPerson(site, expedListPeople[person], expedListPeopleOrig[person])

def updateGratTexts(site):
    global expedListGrats
    re_text = Expedition.RE_USERTEXT.pattern + ".*?" + Expedition.RE_USERTEXT.pattern
    RE_USERTEXT_COMMENT = re.compile(re_text, re.DOTALL)
    grat_hash = getGratList(site)
    for grat in grat_hash.keys():
      if(len(grat) > 0):
        if (expedListGrats[grat] == expedListGratsOrig[grat]):
          print "Page", expedListGrats[grat][2], "has not changed, skipping"
          continue
          
        gratExpeds = getExpeditions(site, grat, grat_hash[grat])
        for date in gratExpeds[1].keys():
          matchObj = RE_USERTEXT_COMMENT.search(gratExpeds[1][date])
          if(matchObj != None):
            expedListGrats[grat][1][date] = RE_USERTEXT_COMMENT.sub(matchObj.group(0),expedListGrats[grat][1][date])
        writeExpedListPerson(site, expedListGrats[grat], expedListGratsOrig[grat])

#Write the expedition list for a specific person or graticule
def writeExpedListPerson(site, expedList, expedListOrig):
    page = pywikibot.Page(site, expedList[2])
    if(not page.exists()):
      page_text = u"<!--EXPLIST-->" + u"\n<!--EXPLIST-->"
      page = pywikibot.Page(site, expedList[2])
      page_write(page, page_text, site)
    else:
      page_text = page.get()
    userExpeds = u"<!--EXPLIST-->"
    ExpedDates = expedList[1].keys()
    ExpedDates.sort()

    listlen = None
    matchObj = Expedition.RE_LISTLEN.search(expedList[0])
    if matchObj:
	print matchObj.group(0)
	print matchObj.group(1)
        listlen = matchObj.group(1)
        if(int(listlen) < 0):
            ExpedDates.reverse()

    itera = 0
    for key in ExpedDates:
      itera += 1
      userExpeds += expedList[1][key] + u"\n"
      if listlen and itera == math.fabs(int(listlen)):
          userExpeds += u"<noinclude>\n"

    if listlen and itera >= math.fabs(int(listlen)):
        userExpeds += u"</noinclude>\n"
    userExpeds += u"<!--EXPLIST-->"

    page_text = RE_EXPLIST_COMMENT.sub(userExpeds, page_text)
    page_write(page, page_text, site)    
    
# Define the main function
def main():
    global expedListPeople
    global expedListPeopleOrig
    global expedListGrats
    global expedListGratsOrig
#    wikipedia.verbose = 1
    titleOfPageToLoad = u'2009-06-14_49_-122' # The "u" before the title means Unicode, important for special characters
#    pywikibot.put_throttle.setDelay(5, absolute = True)
#    wikipedia.get_throttle.setDelay(5, absolute = True)

    enwiktsite = pywikibot.getSite('en', 'geohashing') # loading a defined project's page

#    os.unlink("graticules.sqlite")

#    db = GraticuleDatabase.GraticuleDatabase()
    db = GraticuleDatabase.GraticuleDatabase("graticules.sqlite")
    all = db.getAllKeys()

    # catdb = Category.CategoryDatabase()

    pp_list2 = Category(enwiktsite, u"Category:Expedition_planning").articles()
    # pp_list2 = get_all_category_pages(enwiktsite, u"Category:Expedition_planning", catdb)

#Produce a list of all pages from 3 weekdays ago through when coordinates are available
#  by looking at the [[Category:Meetup on YYYY-MM-DD]] pages

    expedListPeople = parseExpedLists(enwiktsite)
    expedListGrats = parseExpedListsGrats(enwiktsite)

    # Save off the original pages so we can only update exped lists if they've changed
    expedListPeopleOrig = copy.deepcopy(expedListPeople)
    expedListGratsOrig = copy.deepcopy(expedListGrats)

    all_text = u""
    first_date_obj = get_last_day_avail(datetime.date.today() + datetime.timedelta(7))
    last_date_obj = first_date_obj
    cur_dates = []
    plan_dates = []
    old_date_list = []
    try:
        for i in range(0,3):
            while (first_date_obj > datetime.date.today()):
                cur_dates.append(first_date_obj.isoformat())
                expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
                expedListPeople = updateExpedLists(expedSums, expedListPeople, first_date_obj.isoformat())
                expedListGrats = updateExpedListsGrats(expedSums, expedListGrats, first_date_obj.isoformat())
                first_date_obj = first_date_obj - datetime.timedelta(1)

            cur_dates.append(first_date_obj.isoformat())
            expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
            expedListPeople = updateExpedLists(expedSums, expedListPeople, first_date_obj.isoformat())
            expedListGrats = updateExpedListsGrats(expedSums, expedListGrats, first_date_obj.isoformat())
            first_date_obj = first_date_obj - datetime.timedelta(1)

            while (first_date_obj.weekday() > 4):
                cur_dates.append(first_date_obj.isoformat())
                expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
                expedListPeople = updateExpedLists(expedSums, expedListPeople, first_date_obj.isoformat())
                expedListGrats = updateExpedListsGrats(expedSums, expedListGrats, first_date_obj.isoformat())
                first_date_obj = first_date_obj - datetime.timedelta(1)

        cur_dates.append(first_date_obj.isoformat())
        expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
        expedListPeople = updateExpedLists(expedSums, expedListPeople, first_date_obj.isoformat())
        expedListGrats = updateExpedListsGrats(expedSums, expedListGrats, first_date_obj.isoformat())
        first_date = first_date_obj.isoformat()

        remove_dates(enwiktsite, cur_dates)

#Get a list of old date pages to update
        old_date_list = get_old_dates(enwiktsite, db)

#This looks at the pages in [[Category:Expedition planning]]
#  and produces the summaries for all the pages for far in the future
        plan_dates = getExpeditionSummaries(pp_list2, db, None, (last_date_obj+datetime.timedelta(1)).isoformat())
        for i in plan_dates.keys():
            cur_dates.append(i)

        if check_banana(enwiktsite) != 0:
            return 1

        updateUserTexts(enwiktsite)
        updateGratTexts(enwiktsite)
    except Exception:

        print "cur_dates: ",cur_dates
        print "plan_dates: ",plan_dates
        print "old_dates: ",old_date_list
        bug_page = pywikibot.Page(enwiktsite, u"User:AperfectBot/BotBugs")
        bug_page_text = bug_page.get()
        bug_page_text = bug_page_text + u"\n== NEW REPORT ==\nDates:\n" + str(cur_dates) + str(plan_dates) + str(old_date_list) + u"\n"

        print bug_page_text
        page_write(bug_page, bug_page_text, enwiktsite)
        traceback.print_exc(file=sys.stdout)

#Create the [[Template:Expedition_summaries/YYYY-MM-DD]] pages for planning page dates
    putExpeditionSummaries(plan_dates, enwiktsite)

#Build up the text for [[Template:Recent_expeditions]]
    recent_expedition_page_name = u"Template:Recent_expeditions"

    recent_exp_page = pywikibot.Page(enwiktsite, recent_expedition_page_name)
    recent_exp_text = recent_exp_page.get()
    recent_exp_res = re.findall("=== \[\[(\d{4}-\d{2}-\d{2}).*?\]\] ===\n([^=]*)", recent_exp_text, re.S)

    recent_exp_hash = {}
    for i in range(0,len(recent_exp_res)):
        recent_exp_hash[recent_exp_res[i][0]] = recent_exp_res[i][1]

    summary_text = u""
    summary_text += u"<noinclude>__NOTOC__</noinclude>\n"

    date_keys = cur_dates
    date_keys.sort()
    date_keys.reverse()
    if (date_keys[0] > last_date_obj.isoformat()):
        summary_text += u"== Upcoming Events ==\n"
    for i in date_keys:
        if (summary_text[len(summary_text)-1] != u"\n"):
            summary_text += u"\n"

        if (i == (datetime.date.today() - datetime.timedelta(1)).isoformat()):
            summary_text += u"== Recent Expeditions ==\n"

        if (i == last_date_obj.isoformat()):
            summary_text += u"== Expeditions Being Planned ==\n"

        if i in recent_exp_hash:
            summary_text += recent_exp_hash[i]
        else:
            summary_text += u"{{Expedition_summaries|" + i + u"}}\n"
            summary_text += u"<!--Insert manual updates below this line.  Manual updates may not contain equal signs-->\n"

    recent_exp_page = pywikibot.Page(enwiktsite, recent_expedition_page_name)
    page_write(recent_exp_page, summary_text, enwiktsite)


def get_all_category_pages(site, title, catdb):
    cat = category.catlib.Category(site, title)
    article_list = cat.articlesList()
    return article_list

if __name__ == '__main__':
    try:
        re_grat = re.compile('\[\[(.*?)\| *([0-9\-]+, *[0-9\-]+) *\(.*?\) *\]\]')
        re_maprough  = '\{\{[gG]raticule\s[^\}]*?map lat="?\+?%s"?lon="?\+?%s"?[^\}]*?\}\}'
        re_noedit = re.compile('\{\{[mM]aintained[^\}]*\}\}')

        UTF8Writer = codecs.getwriter('utf8')
        sys.stdout = UTF8Writer(sys.stdout)

        main()
    finally:
        pywikibot.stopme()

