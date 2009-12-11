import category, re, Expedition
import wikipedia, datetime
from UserListGenerator import *

class ExpeditionSummaries:
  '''
  This contains all important information about a given expedition
  '''
  def __init__(self, site, date, db):
    self.site = site
    self.date = date
    self.pageList = self._getAllCategoryPages()
    self.expedList = []
    self._putExpeditionSummaries(db)

  def _putExpeditionSummaries(self, db):
    allSummaries = []
    for page in self.pageList:
      if(re.match("\d{4}-\d{2}-\d{2} [-0-9]{1,4} [-0-9]{1,4}$", page.title())):
        print "Parsing page",self.pageList.index(page),"of",len(self.pageList),":",page.title()
        exped = Expedition.Expedition(page.site(), page.title(), db)
        self.expedList.append(exped)
#        print exped.subFormat()
        allSummaries.append(exped.getExpeditionSummary())
        

    page = wikipedia.Page(self.site, "Template:Expedition_summaries/" + self.date)
    self._pageWrite(page, u"<noinclude>This page is automatically generated.  Any edits to this page will be overwritten by a bot.\n\n</noinclude>" + "\n\n".join(allSummaries))
    if(datetime.date.today().isoformat() <= self.date):
        self._datePageWrite()

  def _pageWrite(self, page, text):
    if(self._checkBanana() == 0):
#      print "Would put page with",text
      page.put(text, u"Ook.")
    
  def _datePageWrite(self):
    pageText = u"<noinclude>{{date navigation}}</noinclude>\n"
    pageText += u"{{auto coordinates|" + self.date + "}}\n"
    pageText += u"{{auto gallery|" + self.date + "}}\n"
    pageText += u"<noinclude>{{expedition summaries|" + self.date + "}}</noinclude>\n"

    page = wikipedia.Page(self.site, self.date)
    if(not page.exists()):
      self._pageWrite(page, pageText)

  def _checkBanana(self):
    checkPage = wikipedia.Page(self.site, "User:AperfectBot")
    checkText = checkPage.get(True)
    checkRegex = getSectionRegex(checkText, "distraction banana", False).strip()
    if(len(checkRegex) == 0):
      return 0
    else:
      return 1

  def getSubFormats(self, format = None, user = None, userComment = None):
    formats = {}
    for exped in self.expedList:
      resultText = None
      resultText = exped.subFormat(format, user, userComment)
      if (resultText != None):
        formats[exped.getPagename()] = resultText

    return formats

  def _getAllCategoryPages(self):
    cat = category.catlib.Category(self.site, "Meetup on " + self.date)
    articleList = cat.articlesList()
    return articleList
