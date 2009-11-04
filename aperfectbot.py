import sys
sys.path

import wikipedia
import re
import string
import GraticuleDatabase
import sys
import category
import datetime
import hashlib
import struct
import urllib
import time

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

#Get up to 3 update requests from the page
def get_old_dates(site):
    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()

    matches = re.findall("(''')?(\d{4}-\d{2}-\d{2})(''')?", all_text)

    all_text = re.sub("(''')?(\d{4}-\d{2}-\d{2})(''')?", "'''\g<2>'''", all_text, 3)

    match_list = []
    for i in range(0, min(len(matches), 3)):
        match_list.append(matches[i][1])

    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    page_write(page, all_text, site)
    return match_list

#Clear off the dates which were just updated
def remove_dates(site, dates):
    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    all_text = page.get()    

    for i in dates:
        all_text = re.sub("(''')?" + i + "(''')?\n*", "", all_text)

    page = wikipedia.Page(site, u"User:AperfectBot/Update_requests")
    page_write(page, all_text, site)

# Define the main function
def main():
    titleOfPageToLoad = u'2009-06-14_49_-122' # The "u" before the title means Unicode, important for special characters
#    wikipedia.put_throttle.setDelay(10, absolute = True)
#    wikipedia.get_throttle.setDelay(10, absolute = True)

    enwiktsite = wikipedia.getSite('en', 'geohashing') # loading a defined project's page

    db = GraticuleDatabase.GraticuleDatabase()
#    db = GraticuleDatabase.GraticuleDatabase(site = enwiktsite)
    all = db.getAllKeys()

    catdb = category.CategoryDatabase()

    pp_list2 = get_all_category_pages(enwiktsite, u"Category:Expedition_planning", catdb)
    pp_list = []

#Produce a list of all pages from 3 weekdays ago through when coordinates are available
#  by looking at the [[Category:Meetup on YYYY-MM-DD]] pages
    all_text = u""
    first_date_obj = get_last_day_avail(datetime.date.today() + datetime.timedelta(7))
    last_date_obj = first_date_obj
    all_dates = {}
    for i in range(0,3):
        while (first_date_obj > datetime.date.today()):
            pp_list += get_all_category_pages(enwiktsite, u"Meetup on " + first_date_obj.isoformat(), catdb)
            all_dates[first_date_obj.isoformat()] = []
            first_date_obj = first_date_obj - datetime.timedelta(1)

        pp_list += get_all_category_pages(enwiktsite, u"Meetup on " + first_date_obj.isoformat(), catdb)
        all_dates[first_date_obj.isoformat()] = []
        first_date_obj = first_date_obj - datetime.timedelta(1)

        while (first_date_obj.weekday() > 4):
            pp_list += get_all_category_pages(enwiktsite, u"Meetup on " + first_date_obj.isoformat(), catdb)
            all_dates[first_date_obj.isoformat()] = []
            first_date_obj = first_date_obj - datetime.timedelta(1)

    pp_list += get_all_category_pages(enwiktsite, u"Meetup on " + first_date_obj.isoformat(), catdb)
    all_dates[first_date_obj.isoformat()] = []
    first_date = first_date_obj.isoformat()

#Get a list of old date pages to update
    old_date_list = get_old_dates(enwiktsite)

    old_dates = {}
    for i in range(0, len(old_date_list)):
        old_dates[old_date_list[i]] = []

    pp_old_list = []
    for i in old_dates.keys():
        pp_old_list += get_all_category_pages(enwiktsite, u"Meetup on " + i, catdb)


#This looks at the pages in [[Category:Meetup on YYYY-MM-DD]]
#  and produces the summaries for them
    for i in range(0,len(pp_list)):
        if(re.match("\d{4}-\d{2}-\d{2} [-0-9]{1,4} [-0-9]{1,4}$", pp_list[i].title())):
            sects = get_page_title_sections(pp_list[i].title())
            page_date = sects[0]
            if (page_date >= first_date):
                if not page_date in all_dates:
                    all_dates[page_date] = []

                print "On page # %d of %d " % (i, len(pp_list)) 
                all_dates[page_date].append(parse_planning_page(pp_list[i], db))

#This looks at the pages in [[Category:Expedition planning]]
#  and produces the summaries for all the pages for far in the future
    for i in range(0,len(pp_list2)):
        if(re.match("\d{4}-\d{2}-\d{2} [-0-9]{1,4} [-0-9]{1,4}$", pp_list2[i].title())):
            sects = get_page_title_sections(pp_list2[i].title())
            page_date = sects[0]
            if (page_date > last_date_obj.isoformat()):
                if not page_date in all_dates:
                    all_dates[page_date] = []

                print "On page # %d of %d " % (i, len(pp_list2)) 
                all_dates[page_date].append(parse_planning_page(pp_list2[i], db))

#This looks at old expeditions pages in [[Category:Meetup on YYYY-MM-DD]]
#  and produces the summaries for them
    for i in range(0,len(pp_old_list)):
        if(re.match("\d{4}-\d{2}-\d{2} [-0-9]{1,4} [-0-9]{1,4}$", pp_old_list[i].title())):
            sects = get_page_title_sections(pp_old_list[i].title())
            page_date = sects[0]

            print "On page # %d of %d " % (i, len(pp_old_list))
            if page_date in old_dates:
                old_dates[page_date].append(parse_planning_page(pp_old_list[i], db))

    date_keys = all_dates.keys()
    date_keys.sort()
    date_keys.reverse()
    for i in date_keys:
        all_text += u"=== [[" + i + u"]] ===\n"
        for j in range(0,len(all_dates[i])):
            all_text += all_dates[i][j] + u"\n\n"

    if check_banana(enwiktsite) != 0:
        return 1

#Create the [[Template:Expedition_summaries/YYYY-MM-DD]] pages
    for i in date_keys:
        all_text = u"<noinclude>This page is automatically generated.  Any edits to this page will be overwritten by a bot.\n\n</noinclude>"
        for j in range(0,len(all_dates[i])):
            if(j != 0):
                all_text += u"\n\n"
            all_text += all_dates[i][j]
        page = wikipedia.Page(enwiktsite, "Template:Expedition_summaries/" + i)
        page_write(page, all_text, enwiktsite)
#Only update the date page if its in the future, and its 9:** AM
        if(datetime.date.today().isoformat() <= i):
#            if(time.localtime()[3] == 9):
                date_page_write(i, enwiktsite)

#Create the old [[Template:Expedition_summaries/YYYY-MM-DD]] pages
    old_keys = old_dates.keys()
    for i in old_keys:
        if(len(old_dates[i]) != 0):
            all_text = u"<noinclude>This page is automatically generated.  Any edits to this page will be overwritten by a bot.\n\n</noinclude>"
            all_text += u"\n\n".join(old_dates[i])
            page = wikipedia.Page(enwiktsite, "Template:Expedition_summaries/" + i)
            page_write(page, all_text, enwiktsite)
#            date_page_write(i, enwiktsite)

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

#get rid of the old dates from the update list
    remove_dates(enwiktsite, old_dates.keys())

#This will look for all unique user tags on a page, and make a list out of them.
def get_user_list(text):
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

#This should tell us how long a link will appear when it is replaced by text.
def link_length(link_text):
    act_length = len(link_text)
    if(link_text[0] != "["):
        return act_length
    if((act_length > 1) and (link_text[1] != "[")):
        match_obj = re.match("^[^ ]* ([^\]]+)\]", link_text)
        if((match_obj != None) and (len(match_obj.group(1)) != 0)):
            return len(match_obj.group(1))
        else:
            return 0
    else:
        match_obj = re.match("^[^|]*\|([^\]]+)\]\]", link_text)
        if((match_obj != None) and (len(match_obj.group(1)) != 0)):
            return len(match_obj.group(1))
        else:
            return 0


def get_location(location_text):
    new_loc_arr = re.split("\n", location_text)
    space = u" "
#Strip full comments
    new_loc_text = re.sub("\<\!\-\-.*?\-\-\>+", "", space.join(new_loc_arr), re.S)
#Strip the beginning of a comment to the end of the text
    new_loc_text = re.sub("\<\!\-\-.*$", "", new_loc_text, re.S)
#Strip the begining of the text to the end of a comment
    new_loc_text = re.sub("^.*\-\-\>", "", new_loc_text, re.S)
#Strip nested templates
    new_loc_text = re.sub("\{\{[^}]*?\{\{.*?\}+.*?\}+", "", new_loc_text, re.S)
#Strip templates and tables
    new_loc_text = re.sub("\{+.*?\}+", "", new_loc_text, re.S)
#Strip images and cats
    new_loc_text = re.sub("\[\[(Image|Category):.*?\]\]", "", new_loc_text, re.S)
#Strip html tags
    new_loc_text = re.sub("\<+.*?\>+", "", new_loc_text, re.S)
#Strip extra section headers  A.K.A. Easter Bunny on a unicycle
    new_loc_text = re.sub("=+.*?=+", "", new_loc_text, re.S)
#Get rid of : and * at the beginning of lines
    new_loc_text = re.sub("^[*:]+", "", new_loc_text, re.S)
#Get rid of "this hashpoint" type messages
    new_loc_text = re.sub("(The|This|Today's)\s+?(location|hash ?point|geo ?hash)\s+?(is)?", "", new_loc_text, re.I)
#Strip __NOTOC__
    new_loc_text = string.strip(re.sub("__NOTOC__", "", new_loc_text, re.S))

    res_text = u""
    res_text_len = 0
    iter_len = 1
#This is to allow for links in the location text.
#Only full links should be included.
    while((res_text_len < 75) and (len(new_loc_text) > 0) and (iter_len != res_text_len)):
        iter_len = res_text_len
        match_obj = re.match("^([^[]*?)(http:|\[|$)", new_loc_text)
	if(match_obj != None):
            new_loc_text = new_loc_text[len(match_obj.group(1)):len(new_loc_text)]
        if((match_obj != None) and (len(match_obj.group(1)) != 0)):
            res_text += match_obj.group(1)[0:min(len(match_obj.group(1)),75-res_text_len)]
            res_text_len += min(len(match_obj.group(1)),75-res_text_len)

        if(res_text_len < 75):
            match_obj = re.match("^(\[+[^\]]*\]+|http:\S*)", new_loc_text)
            new_loc_text = re.sub("^(\[+[^\]]*\]+|http:\S*)", "", new_loc_text)
            if((match_obj != None) and (len(match_obj.group(0)) != 0)):
                res_text += match_obj.group(0)
                res_text_len += link_length(match_obj.group(0))

    if(res_text_len >= 75):
        res_text += u"..."

    return res_text

#Assemble each of the individual parts of an expedition description
#  into a single, one line, string.
def assemble_parts(page_title, people_text, location_text, db):
#Get the graticule name from All Graticules
    title_parts = get_page_title_sections(page_title)
    date = title_parts[0]
    lat = title_parts[1]
    lon = title_parts[2]
    name_list = db.getLatLon(lat,lon)
    if((name_list == None) or (name_list[1] == None) or (name_list[2] == None)):
        name = u"Unknown (" + lat + u", " + lon + u")"
    else:
        name = name_list[1] + u", " + name_list[2]

    if(len(people_text) == 0):
        if(datetime.date.today().isoformat() <= date):
            people_text = u"Someone is, why not join them?"
        else:
            people_text = u"Someone went"


    if(len(location_text) == 0):
        if(datetime.date.today().isoformat() <= date):
            location_text = u"Description unavailable, why not have a spontaneous adventure?"
        else:
            location_text = u"Somewhere"

    link = u"[[" + page_title + u"|" + name + u"]]"
    ret_val = link + u" - " + people_text + u" - " + location_text
    return ret_val

#This will return a hash of the most major sections in the provided text
#The keys will be a lower case version of the section title
#The part of the text before the first section header can be accessed with:
#   section_hash[""]
def get_sections(text):
    split_text = re.split("\n", text)
    minlen = 99
    for line in split_text:
        match = re.match("\s*=+", line)
        if ((match != None) and (len(string.strip(match.group(0))) < minlen)):
            minlen = len(string.strip(match.group(0)))

    equal_str = u""  
    for i in range(0,minlen):
        equal_str += u"="
    match_str = u"\n\s*" + equal_str + "([^=]*?)" + equal_str

    text_arr = re.split(match_str, text)
    for i in range(0,len(text_arr)):
        text_arr[i] = string.strip(text_arr[i])

    section_hash = {}
    section_hash[""] = text_arr[0]

    for i in range(1,len(text_arr),2):
        section_hash[string.lower(text_arr[i])] = text_arr[i+1]

    return section_hash

#This will look for a section with one of the names in name_arr
#The search is case insensitive, and returns the first match,
#  starting from name_arr[0] and continuing to name_arr[len(name_arr)-1]
#It will return the body of the appropriate section, or None if
#  there were no matches for the section name.
def get_section(text, name_arr):
    sections = get_sections(text)
    for header in name_arr:
        if(header in sections):
            return sections[header]
    if ((len(name_arr) == 0) and ("" in sections)):
        return sections[""]
    return None

def get_section_regex(text, regex_text):
    sections = get_sections(text)
    if ((regex_text == None) and ("" in sections)):
        return sections[""]
    else:
        for keys in sections.keys():
            if(re.match(regex_text, keys)):
                return sections[keys]
    return None

#This function will parse a list of users, and return them in a comma separated list.
def get_people_text(text, people_text):
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
        people_text = get_user_list(text)
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

def parse_planning_page(page, db):
#Get the page text
    title = page.title()
    wikipedia.output(u'Loading %s...' % title)
#    page = wikipedia.Page(site, title)
    if (page.isRedirectPage()):
        return u""
    text = page.get()
    wikipedia.output(u'Parsing %s...' % title)

    if(text[0] == u"="):
        text = u"\n" + text

    if(text[1] == u"="):
        text = u"\n" + text

#Generate the list of people
#First look in appropriately named "who" sections
    people_sec_text = get_section_regex(text, "(participants?|people)\??")
    if(people_sec_text != None):
        people_text = get_people_text(text, people_sec_text)

#If that fails, look for all unique [[User:*]] tags in the expedition page
    if((people_sec_text == None) or (len(people_text) == 0)):
        people_text = get_user_list(text)

#Generate the Location text
#First look in appropriately named "where" sections
    location_sec_text = get_section_regex(text, "(location|where|about)\??")

#If that fails, look in appropriately named "expedition" sections
    if ((location_sec_text == None) or (len(get_location(location_sec_text)) == 0)):
        location_sec_text = get_section_regex(text, "expeditions?")

#If that fails, look before any section headers
    if ((location_sec_text == None) or (len(get_location(location_sec_text)) == 0)):
        location_sec_text = get_section_regex(text, None)

    if(location_sec_text != None):
        location_text = get_location(location_sec_text)
    else:
        location_text = ""

    return assemble_parts(title, people_text, location_text, db)


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

