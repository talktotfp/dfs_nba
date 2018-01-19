# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 17:47:30 2018

@author: tpauley
"""

import bs4
import requests
import pandas as pd
from string import ascii_lowercase
from sqlalchemy import types, create_engine
from dateutil.parser import parse

#######################################################
### DB connection strings config
#######################################################
tns = """
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = localhost)(PORT = 1522))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = xe)
    )
  )
"""

usr = "nba"
pwd = ""
engine = create_engine('oracle+cx_oracle://%s:%s@%s' % (usr, pwd, tns))


#HTML Settings for Scraping Tables
tableHead = 'thead'
tableHeadRow = 'tr'
tableHeadCell = 'th'
tableBody = 'tbody'
tableBodyRow = 'tr'
tableBodyCell = 'td'

#Check if incoming string is a number
def isNumber(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False

#Standard table scraper with slight tweaks to accomodate specific pages    
def table_scrape(returnType,url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell):
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text,"lxml")
        
    if returnType == 'header':
        head = soup.find(tableHead)
        headers = head.find(tableHeadRow).find_all(tableHeadCell)
        headerList = []
        headerList.append('BREF_ID')
        for iHeaders in headers:
            headerList.append(str.replace(iHeaders.string.upper(),' ','_')) 
        return headerList
    
    if returnType == 'body':
        body = soup.find(tableBody)
        rows = body.find_all(tableBodyRow)
        rowList = []
        for x, iRows in enumerate(rows):
            cellList = []
            for y, a in enumerate(rows[x].find_all('a', href=True)):
                if a.get_text(strip=True) and y == 0: 
                    cellList.append(a['href'])
            for i, iCell in enumerate(iRows):
                cellList.append(iCell.string)
            rowList.append(cellList)
        return rowList


#Loop through A-Z for all player pages
for letter in ascii_lowercase:
    if letter != 'x':       #there are no players with last name X
        url = 'https://www.basketball-reference.com/players/'+letter+'/'   #append letter to URL
        
        #scrape headers and table data from page
        header = table_scrape('header',url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell)
        body = table_scrape('body',url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell)
    
        #check for any blank rows and change any numbers to a float 
        for i,iBody in enumerate(body):
            for x, iCell in enumerate(iBody):
                if iCell is None:
                    body[i][x] = 'N/A'
                else:
                    if isNumber(iCell):
                        body[i][x] = float(iCell)
                        
        if letter == 'a':       #build dataframe on first iteration            
            df = pd.DataFrame(data = body, columns = header)
        else:       #append to dataframe all other iterations
            df2 = pd.DataFrame(data = body, columns = header)
            df = df.append(df2)

#function to parse dates or return null            
def dateParser(stringIn):
    try:
        x = parse(stringIn)
        return x
    except:
        return None       
applyDateParser = lambda x: dateParser(x)

#transform date fields from strings
df['BIRTH_DATE'] = df['BIRTH_DATE'].apply(applyDateParser)
#cut the link to retrieve only the basketball reference ID
df['BREF_ID'] = df['BREF_ID'].apply(lambda x: str.replace(x[11:],'.html',''))  

#prepare datatype for SQL insertion 
dtyp = {c:types.VARCHAR(df[c].str.len().max())
        for c in df.columns[df.dtypes == 'object'].tolist()}

#perform SQL insertion
try:    
    df.to_sql('players', engine, index=True, index_label = 'ID', if_exists='replace',dtype=dtyp)
except BaseException as e:
    print('Failed to write to Oracle: '+ str(e))

