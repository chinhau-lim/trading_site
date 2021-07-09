'''
	This code is developed by Chin Hau Lim.


	-- Goal: 
			1. Scrape Companies that Release their Earnings within date range.
			2. Inject Historical Data into Historical Dates & Historical Data Tables.
			   ~ Date Range: Jan 01, 2021 - May 01, 2021

'''


import requests
import datetime
import numpy as np
import pandas as pd
from time import sleep
from stem import Signal
from bs4 import BeautifulSoup
from selenium import webdriver
from stem.control import Controller
from selenium.webdriver.common.by import By
from connect_db import Database_Connection 
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Inject_Historical_Data:

	def __init__(self):
		''' Declare & Initialize Variables. '''
		self.todays_date = datetime.date.today()
		self.date_range  = list()
		self.main_df     = None
		self.browser     = None

	def switchIP(self):
		'''Signal TOR browser for a new connection.'''
		with Controller.from_port(port = 9151) as controller:
			controller.authenticate()
			controller.signal(Signal.NEWNYM)

	def my_proxy(self):
		'''Get a new selenium webdriver with tor as the proxy.'''		
		fp = webdriver.FirefoxProfile()
		# Direct = 0, Manual = 1, PAC = 2, AUTODETECT = 4, SYSTEM = 5
		fp.set_preference("network.proxy.type", 1)
		fp.set_preference("network.proxy.socks","127.0.0.1")
		fp.set_preference("network.proxy.socks_port",int(9150))
		fp.update_preferences()
		return webdriver.Firefox(firefox_profile=fp)

	def generate_date_range(self, start_date, end_date):
		''' Generate the date range where we want to get those historical data.'''
		self.date_range = [start_date + datetime.timedelta(days=no) for no in range(0, (end_date-start_date).days + 1)]
		return self.date_range

	def get_historical_date(self):
		'''Scrape historical data & return a Panda dataframe.'''
		self.browser = self.my_proxy()
		self.switchIP()

		ticker_checker = set()
		l_01, l_02, l_03 = [], [], []
		l_04, l_05, l_06, l_07 = [], [], [], []

		for date in self.date_range:

			url = "https://finance.yahoo.com/calendar/earnings?day=" + str(date)
			self.browser.get(url)
			soup = BeautifulSoup(self.browser.page_source, "html.parser")

			if soup.find('span', {'class': "Mstart(15px) Fw(500) Fz(s)"}) is None:
				continue

			# Get the total number of earning releases on that day.
			total = int(soup.find('span', {'class': "Mstart(15px) Fw(500) Fz(s)"}).text.split(" ")[-2])
			quotient, remainder = total//100 + 1, total%100
			print("Scraping Date: ", date, " , Total Earning Releases: ", total)

			for no in range(0, quotient):
				if no != 0:
					tno = no * 100
					turl = urls + '&offset=' + str(tno) + '&size=100'
					self.browser.get(turl)
					soup = BeautifulSoup(self.browser.page_source, "html.parser")

				for content in soup.find_all('tr', {'class': "simpTblRow Bgc($hoverBgColor):h BdB Bdbc($seperatorColor) Bdbc($tableBorderBlue):h H(32px) Bgc($lv2BgColor)"}):
					if content.find('a', {'data-test': 'quoteLink'}).text not in ticker_checker:
						l_01.append(date)
						l_02.append(content.find('a', {'data-test': 'quoteLink'}).text)
						l_03.append(content.find('td', {'aria-label': 'Company'}).text)
						l_04.append(content.find('td', {'aria-label': 'EPS Estimate'}).text)
						l_05.append(content.find('td', {'aria-label': 'Reported EPS'}).text)
						l_06.append(content.find('td', {'aria-label': 'Surprise(%)'}).text)
						temp = content.find('a', {'data-test': 'quoteLink'}).get('href')
						temp = temp.split('?p=')
						temp = 'https://finance.yahoo.com' + temp[0] + '/history?p=' + temp[1]
						l_07.append(temp)
						ticker_checker.add(content.find('a', {'data-test': 'quoteLink'}).text)
					
				for content in soup.find_all('tr', {'class': "simpTblRow Bgc($hoverBgColor):h BdB Bdbc($seperatorColor) Bdbc($tableBorderBlue):h H(32px) Bgc($lv1BgColor)"}):
					if content.find('a', {'data-test': 'quoteLink'}).text not in ticker_checker:
						l_01.append(date)
						l_02.append(content.find('a', {'data-test': 'quoteLink'}).text)
						l_03.append(content.find('td', {'aria-label': 'Company'}).text)
						l_04.append(content.find('td', {'aria-label': 'EPS Estimate'}).text)
						l_05.append(content.find('td', {'aria-label': 'Reported EPS'}).text)
						l_06.append(content.find('td', {'aria-label': 'Surprise(%)'}).text)
						temp = content.find('a', {'data-test': 'quoteLink'}).get('href')
						temp = temp.split('?p=')
						temp = 'https://finance.yahoo.com' + temp[0] + '/history?p=' + temp[1]
						l_07.append(temp)
						ticker_checker.add(content.find('a', {'data-test': 'quoteLink'}).text)

		main_dic = {'er_date': l_01, 'tickers': l_02, 'company_name': l_03, 'urls': l_07, 'eps_estimate': l_04,\
					'reported_eps': l_05, 'surprise': l_06}
		self.main_df = pd.DataFrame(main_dic)
		return

	def get_historical_price(self):

		def helper_func(edate, urls):

			self.browser.get(urls)
			inner_soup = BeautifulSoup(self.browser.page_source, "html.parser")
			prev, curr = [], []

			for content in inner_soup.find_all('tr', {'class': 'BdT Bdc($seperatorColor) Ta(end) Fz(s) Whs(nw)'}):
	
				dt = content.find('td', {'class': 'Py(10px) Ta(start) Pend(10px)'}).text
				dt = datetime.datetime.strptime(dt, '%b %d, %Y').date()
				ddiff = (dt - edate).days
				
				if ddiff < -15:
					break

				if -10 < ddiff < 5: 
					temp = []
					prices = content.find_all('td', {'class':"Py(10px) Pstart(10px)"})
					for p in prices:
						temp.append(p.text)
						if len(temp) == 6:
							hp = None
							if temp[1] != '-':
								temp[1] = temp[1].replace(",", "")
								hp = float(temp[1])
								if 0 <= ddiff < 5:
									curr.append(hp)
								else:
									prev.append(hp)
	
			if len(prev) == 0 or len(curr) == 0:
				return None, None
			return max(prev), max(curr)

		self.main_df['pmax'], self.main_df['cmax'] = np.vectorize(helper_func)(self.main_df['er_date'], self.main_df['urls'])

	def logistics(self):

		def classification(val):
			''' Gain(2), No Change(1), Lost(0).'''

			if -0.09 <= val <= 0.09:
				return 1
			elif val > 0.09:
				return 2
			elif val < -0.09:
				return 0
			return None

		print(self.main_df.shape)
		self.main_df = self.main_df[self.main_df['pmax'].notna()]
		self.main_df = self.main_df[self.main_df['cmax'].notna()]
		print(self.main_df.shape)
		self.main_df['price_diff'] = self.main_df['cmax'] - self.main_df['pmax']
		self.main_df['perct_diff'] = (self.main_df['price_diff'] / self.main_df['pmax']) * 100
		self.main_df['status'] = self.main_df['price_diff'].apply(classification)
		self.main_df.to_csv('sample_data.csv')
		return

	def insert_to_database(self):
		'''Insert scraped data into our database.'''
		dc = Database_Connection()
		conn = dc.get_conn_engine()
		self.main_df = self.main_df[['er_date', 'tickers', 'company_name', 'urls', 'eps_estimate',\
					                 'reported_eps', 'surprise', 'pmax', 'cmax', 'price_diff', 'perct_diff',\
					                 'status']]
		self.main_df.columns = dc.get_table_columns('historical_data')
		self.main_df.to_sql('historical_data', con=conn, if_exists='append', index=False)
		return 


if __name__ == '__main__':
		
	ihd = Inject_Historical_Data()
	start_date, end_date = datetime.date(2021, 6, 23), datetime.date(2021, 7, 1)
	ihd.generate_date_range(start_date, end_date)
	ihd.get_historical_date()
	ihd.get_historical_price()
	ihd.logistics()
	ihd.insert_to_database()

