# -*- coding: utf-8 -*-
"""
Created on Sun Mar 21 11:27:06 2021

@author: Fabian Schlueter

Thanks to Christopher Buhtz from statisquo.de
His article serves as foundation for this crawler:
https://statisquo.de/2020/01/16/autoscout24-mining-webscraping-mit-python/
"""

# Import packages
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import re

# Paths
filename = 'Porsche'   # e.g. name of the car brand or type you search for
path = r'C:\\' + filename + '.xlsx'   # select path for saving data

# URL of first result oage of search
# Go to https://www.autoscout24.de and enter your search terms. Select order by age descending.
start_page = 'https://www.autoscout24.de/lst/porsche/911?sort=age&desc=1&offer=J%2CU%2CO%2CD&ustate=N%2CU&size=20&page=1&cy=D&atype=C&fc=1&qry=&'

# Existing data of previous search?
# New results will be appended.
try:
    df = pd.read_excel(path)
except FileNotFoundError:
    df = pd.DataFrame()


#%%

# Loop over 20 result pages
for i in range(1,21):
    # Read single page
    print('Reading SRP ' + str(i) + '.')
    # Split up url of start page to fill in current value of i.
    response = requests.get(start_page.split('page=1')[0] + 'page=' + str(i) + start_page.split('page=1')[1])
    html = response.text
    
    doc = BeautifulSoup(html, 'html.parser')
    
    # Get urls of all results on current page.
    offer_list = []
    for paragraph in doc.find_all('a'):
        # Only interested in actual offers (angebote), not in leasing nor recommendation
        if r'/angebote/' in str(paragraph.get('href')) and r'/leasing/' not in str(paragraph.get('href')) and r'/recommendation/' not in str(paragraph.get('href')):
            offer_list.append(paragraph.get('href'))
    
    # Drop urls that were already crawled. These are in df["url"], if df exists from preivous search.
    offer_list_unreduced = offer_list # Just for checking
    try:
        offer_list = [item for item in offer_list if 'https://www.autoscout24.de' + item not in list(df["url"])]
    except:
        print("First results for this search.")

    # Loop over offers.
    for item in offer_list:
        try:
            url = 'https://www.autoscout24.de' + item
            response = requests.get(url)
            html = response.text
            
            doc = BeautifulSoup(html, 'html.parser')
            
            # Empty dictionary for saving car's main features
            car_dict = {}
            
            # Names of main features are within dt tags of html. Their value is always in the following dd tag.
            for key, value in zip(doc.find_all('dt'), doc.find_all('dd')): # Combine every dt tag with the following dd tag by zip.
                car_dict[key.text.replace("\n", "")] = value.text.replace("\n", "") # Save in dict.
            
            # Following features must be identified separateley.
            
            # professional seller?
            car_dict['haendler'] = doc.find("div", attrs={"class":"cldt-vendor-contact-box",
                                                          "data-vendor-type":"dealer"}) != None
            
            # private seller?
            car_dict['privat'] = doc.find("div", attrs={"class":"cldt-vendor-contact-box",
                                                          "data-vendor-type":"privateseller"}) != None
            # city of sale incl. zip-code
            car_dict['ort'] = doc.find("div", attrs={"class":"sc-grid-col-12",
                                                          "data-item-name":"vendor-contact-city"}).text
            # driven miles
            car_dict['miles'] = html.split('"stmil" : ')[1].replace("\n", '').split(',')[0].strip()
            
            # price
            car_dict['price'] = "".join(re.findall(r'[0-9]+',doc.find("div",attrs={"class":"cldt-price"}).text))
            
            # save url and time of program's execution
            car_dict['url'] = url
            car_dict['date'] = datetime.now().strftime("%Y-%m-%d")
            car_dict['time'] = datetime.now().strftime("%H-%M-%S")
            
            # add several features that have no value. These either exist in the current car or not (e.g. air-con, radio, leather seatings, etc.)
            for j in doc.find_all('div', attrs={"class":"cldt-equipment-block sc-grid-col-3 sc-grid-col-m-4 sc-grid-col-s-12 sc-pull-left"}):
                for span in j.find_all('span'):
                    car_dict[span.text] = 1 # assign value of 1 if feature exists.

            # append data of current car to dataframe
            car_car_dict = {}
            car_car_dict['URL'] = car_dict
            df_append = pd.DataFrame(car_car_dict).T
            df=df.append(df_append)   
            
        except Exception as e:
            print(str(e))

    print('Appended data from SRP ' + str(i) + '.')


# save dataframe as excel
df.to_excel(path, index=False)