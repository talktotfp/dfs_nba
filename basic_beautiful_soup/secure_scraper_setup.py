# -*- coding: utf-8 -*-
"""
Created on Tue Mar  6 22:52:11 2018

@author: tpauley
"""
import bs4
import requests
import pandas as pd
from datetime import timedelta, date
from sqlalchemy import types, create_engine
import cx_Oracle

def test():
    return('abc')
    
def alchemyCreator():   
#info for database connection (as TNS config) (used for SQLAlchemy inserts)
    tns = """
      (DESCRIPTION =
        (ADDRESS = (PROTOCOL = TCP)(HOST = www.tylerpauley.com)(PORT = 1521))
        (CONNECT_DATA =
          (SERVER = DEDICATED)
          (SERVICE_NAME = xe)
        )
      )
    """
    usr = "dfs"
    pwd = "rp4490"
    engine = create_engine('oracle+cx_oracle://%s:%s@%s' % (usr, pwd, tns))
    return engine

def oracleCreator(): 
#open first Oracle connection in Cx_Oracle
    ip = 'www.tylerpauley.com'
    port = 1521
    SID = 'xe'
    dsn_tns = cx_Oracle.makedsn(ip, port, SID)
    oracle_con = cx_Oracle.connect('dfs', 'rp4490', dsn_tns)
    return oracle_con
    
#function to check if is a number
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

#standard table scraping function
def table_scrape(returnType,url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell):
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text,"lxml")
    head = soup.find(tableHead)
    headers = head.find(tableHeadRow).find_all(tableHeadCell)
    headerList = []
    for iHeaders in headers:
        headerList.append(iHeaders.string) 
        
    body = soup.find(tableBody)
    rows = body.find_all(tableBodyRow)
    rowList = []
    for iRows in rows:
        cellList = []
        for iCell in iRows:
            cellList.append(iCell.string)
        rowList.append(cellList)
        
        
    if len(headers) != len(rowList[0]):
        print('Warning: Number of columns in header (' + str(len(headers)) + ') does not match body(' + str(len(rowList[0])) + ')')
    if returnType == 'header':
        return headerList
    if returnType == 'body':
        return rowList
    if returnType == 'df' and len(headers) == len(rowList[0]):
        df = pd.DataFrame(data = rowList[0]).T
        df.columns = headerList
        return df

#function to build list of URLs based on the date delta of TODAY and MAX_DATE from gamelog
def dateDiff (month,day,year):
    def daterange(date1, date2):
        for n in range(int ((date2 - date1).days)+1):
            yield date1 + timedelta(n)
    
    date_list = []
    start_dt = date(year, month, day)
    end_dt = date(date.today().year,date.today().month, date.today().day)
    for dt in daterange(start_dt, end_dt):
        date_list.append('https://www.basketball-reference.com/friv/dailyleaders.fcgi?month='+str(dt.month)+'&day='+str(dt.day)+'&year='+str(dt.year))
    return date_list[:-1]    