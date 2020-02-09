# How to set up aperfectbot:

1. Get a bot user.
	1. This makes it so the bot's edits don't flood recent changes on the wiki, and makes it apparent that these edits were done automatically.
1. Get pywikibot set up
	1. Download pywikibot module.
	1. Follow these instructions to set up the bot framework https://www.mediawiki.org/wiki/Manual:Pywikibot/Use_on_third-party_wikis
		1. Generate the geohashing family based on those instruction.
		1. Use the login script to log into the bot, then it should save a cookie so that it can keep operating in the background forever.
1. Generate a full date list
	* This is for automatic updating of old date pages.
	* `python datelist_gen.py > aperfectbot_updates.txt`
1. Generate the graticules database
	* This took about 15 minutes last time I ran it
	* `python pwb.py /path/to/pygeohashing/buildGraticuleDatabase.py`
	* It will count up multiple times, one for each "All Graticules" page.
1. Manually run the bot once
	* Run it in the directory you intend to run it from normally, to ensure things are going well
	* Check the recent changes on the wiki to see if there are a bunch of destructive edits.
	* `python pwb.py /path/to/pygeohashing/aperfectbot.py`
1. Start up a cron job to run the bot automatically
	* Here's the one I used forever:
```* * * * * cd /path/to/pywikibot; if [ ! -e aperfectbot.lock ]; then date > aperfectbot.lock; python pwb.py /path/to/pygeohashing/aperfectbot.py >output.txt 2>&1 ; rm aperfectbot.lock; fi```
