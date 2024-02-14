import datetime

date_list = []

cur_date = datetime.date.today()
first_date = datetime.date(2008,5,21)

while(cur_date >= first_date):
	print(cur_date.isoformat())
	cur_date -= datetime.timedelta(1)

