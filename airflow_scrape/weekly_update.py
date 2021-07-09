import requests
import datetime
import numpy as np
import pandas as pd
from time import sleep
from bs4 import BeautifulSoup
from selenium import webdriver
from stem.control import Controller
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Web_Scraper:

	def __init__(self):

		self.monday_list = None
		self.todays_date = None
		self.historical_drange = None
		self.futuristic_drange = None
		self.historical_urls = dict()
		self.futuristic_urls = dict()
		self.h_df = None


		self.past_companies_01 = []
		self.past_companies_02 = []
		self.curr_companies_01 = []
		self.curr_companies_02 = []

	def generate_mondays(self):
		'''
			This helper function returns all Sunday in 2021.
			
			- timedelta : duration expressing the difference between 2 datetime instances.
			- weekday   : return the day of the week as an integer where Monday is 0 and Sunday is 6.

			Why do we choose to start on Monday? 
			- Most stock exchanges operate on weekdays.
			- So we want our users to be able to make decisions in advance, Monday - Sunday period.
		'''	
		start_date, end_date = datetime.date(2021, 5, 1), datetime.date(2022, 3, 1)
		self.monday_list = [start_date + datetime.timedelta(days=i) for i in range((end_date - start_date).days)\
			   		   		if (start_date + datetime.timedelta(days=i)).weekday() == 0]
		return 

	def get_todays_date(self):
		'''Self explanatory.'''
		self.todays_date = datetime.date.today()
		return 

	def get_compare_date(self):
		'''
			Compare today's date with list of mondays.
			Return this week's earnings til next 2 weeks' earnings. 			
		'''
		index = 0
		for i, date in enumerate(self.monday_list):
			if date >= self.todays_date:
				index = i
				break
		h0, h1, h2 = index - 3, index - 2, index - 1 		
		i0, i1, i2 = index - 1, index, index + 1
		
		mon0, mon1, mon2 = self.monday_list[h0], self.monday_list[h1], self.monday_list[h2]
		self.historical_drange = [mon0, mon1, mon2]

		mon0, mon1, mon2 = self.monday_list[i0], self.monday_list[i1], self.monday_list[i2]
		self.futuristic_drange = [mon0, mon1, mon2]
		return

	def get_links(self):
		'''  
			https://finance.yahoo.com/calendar/earnings?from=2021-05-23&to=2021-05-29&day=2021-05-24
		'''
		for out in range(1, 3):
			for inner in range((self.historical_drange[out] - self.historical_drange[out-1]).days):
				curr = self.historical_drange[out-1] + datetime.timedelta(days=inner)
				self.historical_urls[curr] = "https://finance.yahoo.com/calendar/earnings?day=" + str(curr)
				

		for out in range(1, 3):
			for inner in range((self.futuristic_drange[out] - self.futuristic_drange[out-1]).days):
				curr = self.futuristic_drange[out-1] + datetime.timedelta(days=inner)
				self.futuristic_urls[curr] = "https://finance.yahoo.com/calendar/earnings?day=" + str(curr)
				#self.futuristic_urls.append("https://finance.yahoo.com/calendar/earnings?day=" + str(curr))
		return

   # signal TOR for a new connection
	def switchIP(self):
		with Controller.from_port(port = 9151) as controller:
			controller.authenticate()
			controller.signal(Signal.NEWNYM)

    # get a new selenium webdriver with tor as the proxy
	def my_proxy(self):
		fp = webdriver.FirefoxProfile()
		# Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
		fp.set_preference("network.proxy.type", 1)
		fp.set_preference("network.proxy.socks","127.0.0.1")
		fp.set_preference("network.proxy.socks_port",int(9150))
		fp.update_preferences()
		return webdriver.Firefox(firefox_profile=fp)

	def get_historical_data(self):
		'''
			Retrieve all historical data. 
			Get tickers link - EPS Estimate, Reported EPS, Surprise(%)
			Get statistics on tickers - 
		'''
		browser = self.my_proxy()
		count, check = 0, set()
		list_01, list_02, list_03, list_04, list_05, list_06 = [], [], [], [], [], []

		for date, urls in self.historical_urls.items():

			browser.get(urls)
			soup = BeautifulSoup(browser.page_source, "html.parser")

			if soup.find('span', {'class': "Mstart(15px) Fw(500) Fz(s)"}) is None:
				continue

			total = int(soup.find('span', {'class': "Mstart(15px) Fw(500) Fz(s)"}).text.split(" ")[-2])
			quotient, remainder = total//100 + 1, total%100

			for i in range(0, quotient):
				if i != 0:
					ti = i * 100
					turl = urls + '&offset=' + str(ti) + '&size=100'
					browser.get(turl)
					soup = BeautifulSoup(browser.page_source, "html.parser")

				for content in soup.find_all('tr', {'class': "simpTblRow Bgc($hoverBgColor):h BdB Bdbc($seperatorColor) Bdbc($tableBorderBlue):h H(32px) Bgc($lv2BgColor)"}):
				    if content.find('a', {'data-test': 'quoteLink'}).text not in check:
				    	count += 1
				    	list_01.append(date)
				    	list_02.append(content.find('a', {'data-test': 'quoteLink'}).text)
				    	list_03.append(content.find('td', {'aria-label': 'Company'}).text)
				    	list_04.append(content.find('td', {'aria-label': 'EPS Estimate'}).text)
				    	list_05.append(content.find('td', {'aria-label': 'Reported EPS'}).text)
				    	list_06.append(content.find('td', {'aria-label': 'Surprise(%)'}).text)
				    	check.add(content.find('a', {'data-test': 'quoteLink'}).text)
				    
				for content in soup.find_all('tr', {'class': "simpTblRow Bgc($hoverBgColor):h BdB Bdbc($seperatorColor) Bdbc($tableBorderBlue):h H(32px) Bgc($lv1BgColor)"}):
				    if content.find('a', {'data-test': 'quoteLink'}).text not in check:
				    	count += 1
				    	list_01.append(date)
				    	list_02.append(content.find('a', {'data-test': 'quoteLink'}).text)
				    	list_03.append(content.find('td', {'aria-label': 'Company'}).text)
				    	list_04.append(content.find('td', {'aria-label': 'EPS Estimate'}).text)
				    	list_05.append(content.find('td', {'aria-label': 'Reported EPS'}).text)
				    	list_06.append(content.find('td', {'aria-label': 'Surprise(%)'}).text)
				    	check.add(content.find('a', {'data-test': 'quoteLink'}).text)

		historical_data = {'date': list_01, 'quote_link': list_02, 'company': list_03, 'eps_estimate': list_04,\
						   'reported_eps': list_05, 'surprise': list_06}
		self.h_df = pd.DataFrame(historical_data)
		print(self.h_df.shape)
		return




	def main_func(self):

		self.generate_mondays()
		self.get_todays_date()
		self.get_compare_date()
		self.get_links()
		self.get_historical_data()
		return 


if __name__ == '__main__':

	ws = Web_Scraper()
	ws.main_func()



