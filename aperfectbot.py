import sys
sys.path

import wikipedia, re, string
import GraticuleDatabase
import sys, category, datetime
import hashlib, struct, urllib
import time
from UserListGenerator import *
import Expedition, ExpeditionSummaries

#ccodes  = {}
#for line in open("countryCodes.txt","r"):
#  data = line.split("\t")
#  ccodes[data[1]]=data[0]

# site = wikipedia.getSite()

# You must pass a date after the last available one
def get_last_day_avail(date):
    djia = urllib.urlopen((date - datetime.timedelta(1)).strftime("http://irc.peeron.com/xkcd/map/data/%Y/%m/%d")).read()
    if djia.find('404 Not Found') >= 0:
        date = get_last_day_avail(date - datetime.timedelta(1))
    return date

#Split the page title up on spaces/underscores
def get_page_title_sections(title):
    return re.split("[ _]+", title)

#Look for the failsafe stop
def check_banana(site):
    check_page = wikipedia.Page(site, "User:AperfectBot")
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
    page.put(text, u"Ook.")

#Write a date page if it doesn't already exist.
def date_page_write(date, site):
    page_text = u"<noinclude>{{date navigation}}</noinclude>\n"
    page_text += u"{{auto coordinates|" + date + "}}\n"
    page_text += u"{{auto gallery|" + date + "}}\n"
    page_text += u"<noinclude>{{expedition summaries|" + date + "}}</noinclude>\n"

    page = wikipedia.Page(site, date)
    if(not page.exists()):
        page_write(page, page_text, site)
        add_date(site, date)

#For displaying dates in a different manner than normal
def holiday_lookup(date):
    if(date == u"2009-07-07"):
        return u"2009-07-07|2009-07-07 (Elbie's Birthday)"
    if(date == u"2009-07-01"):
        return u"2009-07-01|2009-07-01 (Canada Day)"
    if(date == u"2009-07-04"):
        return u"2009-07-04|2009-07-04 (Independence Day, United States of America)"

    else:
        return date

customExpedList = {}

#Get up to 3 update requests from the page
def get_old_dates(site, db):
    global customExpedList

    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()

    matches = re.findall("(''')?(\d{4}-\d{2}-\d{2})(''')?", all_text)

    all_text = re.sub("(''')?(\d{4}-\d{2}-\d{2})(''')?", "'''\g<2>'''", all_text, 3)

    match_list = []
    for i in range(0, min(len(matches), 3)):
        match_list.append(matches[i][1])

    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
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
        customExpedList.update(expedSum.getSubFormats())

    remove_dates(site, match_list)

    return match_list

#Clear off the dates which were just updated
def remove_dates(site, dates):
    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()    

    fh = open("aperfectbot_updates.txt", "r")
    all_text_file = fh.read()
    fh.close()

    for i in dates:
        all_text = re.sub("(''')?" + i + "(''')?\n*", "", all_text)
        all_text_file = re.sub("(''')?" + i + "(''')?\n*", "", all_text_file)
        all_text_file += "\n" + i

    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    page_write(page, all_text, site)

    fh = open("aperfectbot_updates.txt", "w")
    fh.write(all_text_file)
    fh.close()


def add_date(site, date):
    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()    
    all_text += "\n\n" + date
    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
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
        all_text = u"<noinclude>This page is automatically generated.  Any edits to this page will be overwritten by a bot.\n\n</noinclude>"
        all_text += u"\n\n".join(summaries[i])
        page = wikipedia.Page(site, "Template:Expedition_summaries/" + i)
        page_write(page, all_text, site)
#Only update the date page if its in the future, and its 9:** AM
        if(datetime.date.today().isoformat() <= i):
            date_page_write(i, site)

# Define the main function
def main():
    global customExpedList
#    wikipedia.verbose = 1
    titleOfPageToLoad = u'2009-06-14_49_-122' # The "u" before the title means Unicode, important for special characters
#    wikipedia.put_throttle.setDelay(10, absolute = True)
#    wikipedia.get_throttle.setDelay(10, absolute = True)

    enwiktsite = wikipedia.getSite('en', 'geohashing') # loading a defined project's page

    db = GraticuleDatabase.GraticuleDatabase()
    all = db.getAllKeys()

    catdb = category.CategoryDatabase()

    pp_list2 = get_all_category_pages(enwiktsite, u"Category:Expedition_planning", catdb)

#Produce a list of all pages from 3 weekdays ago through when coordinates are available
#  by looking at the [[Category:Meetup on YYYY-MM-DD]] pages

    page = wikipedia.Page(enwiktsite, u"User:AperfectBot/TestPage")
    page_text = page.get()
    formats = [
      (Expedition.RE_DATE,      re.escape(Expedition.date_comment)      + ".*?" + re.escape(Expedition.date_comment)),
      (Expedition.RE_GRATADD,   re.escape(Expedition.gratadd_comment)   + ".*?" + re.escape(Expedition.gratadd_comment)),
      (Expedition.RE_GRATNAME,  re.escape(Expedition.gratname_comment)  + ".*?" + re.escape(Expedition.gratname_comment)),
      (Expedition.RE_PEOPLE,    re.escape(Expedition.people_comment)    + ".*?" + re.escape(Expedition.people_comment)),
      (Expedition.RE_LOCATION,  re.escape(Expedition.location_comment)  + ".*?" + re.escape(Expedition.location_comment)),
      (Expedition.RE_TRANSPORT, re.escape(Expedition.transport_comment) + ".*?" + re.escape(Expedition.transport_comment)),
      (Expedition.RE_REACHED,   re.escape(Expedition.reached_comment)   + ".*?" + re.escape(Expedition.reached_comment)),
      (Expedition.RE_REASON,    re.escape(Expedition.reason_comment)    + ".*?" + re.escape(Expedition.reason_comment)),
      (Expedition.RE_LINK,      re.escape(Expedition.link_comment)      + ".*?" + re.escape(Expedition.link_comment)),
      (Expedition.RE_EXPED,     re.escape(Expedition.exped_comment)     + ".*?" + re.escape(Expedition.exped_comment)),
      (Expedition.RE_USERTEXT,  re.escape(Expedition.usertext_comment)  + ".*?" + re.escape(Expedition.usertext_comment)),
    ]

    formatText = u"(" + Expedition.RE_APECOMMENT.pattern + re.escape(u" date DATE - gratadd GRATADD - gratname GRATNAME - people PEOPLE - location LOCATION - transport TRANSPORT - reached REACHED - reason REASON - link LINK - exped EXPED - usertext USERTEXT\n") + u")"
#    formatText = u"(" + Expedition.RE_APECOMMENT.pattern + u")"
#    formatText = u"(" + re.escape(u" date DATE - gratadd GRATADD - gratname GRATNAME - people PEOPLE - location LOCATION - transport TRANSPORT - reached REACHED - reason REASON - link LINK - exped EXPED - usertext USERTEXT\n") + u")"

    for rex, repl in formats:
      formatText = rex.sub(repl, formatText)

    page_matches = re.findall(formatText, page_text)

    for text, name in page_matches:
      customExpedList[name] = text

    all_text = u""
    first_date_obj = get_last_day_avail(datetime.date.today() + datetime.timedelta(7))
    last_date_obj = first_date_obj
    cur_dates = []
    for i in range(0,3):
        while (first_date_obj > datetime.date.today()):
            cur_dates.append(first_date_obj.isoformat())
            expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
            customExpedList.update(expedSums.getSubFormats())
            first_date_obj = first_date_obj - datetime.timedelta(1)

        cur_dates.append(first_date_obj.isoformat())
        expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
        customExpedList.update(expedSums.getSubFormats())
        first_date_obj = first_date_obj - datetime.timedelta(1)

        while (first_date_obj.weekday() > 4):
            cur_dates.append(first_date_obj.isoformat())
            expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
            customExpedList.update(expedSums.getSubFormats())
            first_date_obj = first_date_obj - datetime.timedelta(1)

    cur_dates.append(first_date_obj.isoformat())
    expedSums = ExpeditionSummaries.ExpeditionSummaries(enwiktsite, first_date_obj.isoformat(), db)
    customExpedList.update(expedSums.getSubFormats())
    first_date = first_date_obj.isoformat()

#    print customExpedList

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

    page = wikipedia.Page(enwiktsite, u"User:AperfectBot/TestPage")
    userExpeds = u""
    ExpedDates = customExpedList.keys()
    ExpedDates.sort()
    for key in ExpedDates:
      userExpeds += customExpedList[key]
    page_write(page, userExpeds, enwiktsite)

#Create the [[Template:Expedition_summaries/YYYY-MM-DD]] pages for planning page dates
    putExpeditionSummaries(plan_dates, enwiktsite)

#Build up the text for [[Template:Recent_expeditions]]
    recent_expedition_page_name = u"Template:Recent_expeditions"

    recent_exp_page = wikipedia.Page(enwiktsite, recent_expedition_page_name)
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

        summary_text += u"=== [[" + holiday_lookup(i) + u"]] ===\n"
        if i in recent_exp_hash:
            summary_text += recent_exp_hash[i]
        else:
            summary_text += u"{{Expedition_summaries|" + i + u"}}\n"
            summary_text += u"<!--Insert manual updates below this line.  Manual updates may not contain equal signs-->\n"

    recent_exp_page = wikipedia.Page(enwiktsite, recent_expedition_page_name)
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

        main()
    finally:
        wikipedia.stopme()

