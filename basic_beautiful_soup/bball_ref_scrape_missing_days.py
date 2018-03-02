# -*- coding: utf-8 -*-
"""
Created on Fri Mar  2 10:20:27 2018

@author: tpauley
"""

import bs4
import requests
import pandas as pd
from sqlalchemy import types, create_engine
import cx_Oracle
from datetime import timedelta, date


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

#open first Oracle connection in Cx_Oracle
ip = 'www.tylerpauley.com'
port = 1521
SID = 'xe'
dsn_tns = cx_Oracle.makedsn(ip, port, SID)
oracle_con = cx_Oracle.connect('dfs', 'rp4490', dsn_tns)
oracle_cur = oracle_con.cursor()

#get max date from gamelog dataset
oracle_query = """select EXTRACT(YEAR from MAX(GAME_DATE)+1) as YEARID,
EXTRACT(MONTH from MAX(GAME_DATE)+1) as MONTHID ,
EXTRACT(DAY from MAX(GAME_DATE)+1) as DAYID 
from NBA_GAMELOG""" #only select 2010 or later
df_date = pd.read_sql_query(oracle_query,oracle_con) #build dataframe from query;

#close cursor and connection
oracle_cur.close()
oracle_con.close()

#define HTML attributes for scraping
tableHead = 'thead'
tableHeadRow = 'tr'
tableHeadCell = 'th'
tableBody = 'tbody'
tableBodyRow = 'tr'
tableBodyCell = 'td'

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
    end_dt = date(datetime.date.today().year, datetime.date.today().month, datetime.date.today().day)
    for dt in daterange(start_dt, end_dt):
        date_list.append('https://www.basketball-reference.com/friv/dailyleaders.fcgi?month='+str(dt.month)+'&day='+str(dt.day)+'&year='+str(dt.year))
    return date_list[:-1]        

#loop through URL's generated by dateDiff using max date query results as inputs
for url in dateDiff(df_date.iloc[0]['MONTHID'],df_date.iloc[0]['DAYID'],df_date.iloc[0]['YEARID']):
    #open a new oracle connection/cursor each loop to avoid timeouts
    ip = 'www.tylerpauley.com'
    port = 1521
    SID = 'xe'
    dsn_tns = cx_Oracle.makedsn(ip, port, SID)
    oracle_con = cx_Oracle.connect('dfs', 'rp4490', dsn_tns)
    oracle_cur = oracle_con.cursor()
    #scrape the page
    try:
        header = table_scrape('header',url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell)
        body = table_scrape('body',url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell)
        
        for i,iBody in enumerate(body):
            if  isNumber(iBody[0]):
                for x, iCell in enumerate(iBody):
                    if iCell is None:
                        body[i][x] = float(0)
                    else:
                        if isNumber(iCell):
                            body[i][x] = float(iCell)
            else:
                    body.remove(iBody)
        df = pd.DataFrame(data = body, columns = header)
        df = df.rename(columns={"Date": "GAME_DATE", "FG%": "FGP", "3P": "TP", "3PA": "TPA", "3P%": "TPP", "+/-": "PM", "FT%": "FTP"}) #get rid of weird characters in column names            
        df = df.fillna(0.0) #fill any blank stats with 0   
        df['MP'] = df['MP'].apply(lambda x: round((float((str(x)+":0").split(":")[0]) + float((str(x)+":0").split(":")[1])/100*1.667),2)) #convert minutes played to number
        df = df.apply(lambda x: x.replace(u'\xa0', u' ')) #replace odd ascii characters to prevent Oracle errors
        #convert number fields to floats (from string objects)
        for col in ['FG','FGA','FGP','TP','TPA','TPP','FT','FTA','FTP','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS','GmSc','MP']:
            df[col] = df[col].apply(lambda x: float(x))

        #extract date from URL
        df['GAME_DATE'] = url.replace('https://www.basketball-reference.com/friv/dailyleaders.fcgi?month=','').replace('&day=','/').replace('&year=','/')    

        #remove unneeded columns           
        df = df[['Rk','Player','Tm','Opp','FG','FGA','FGP','TP','TPA','TPP','FT','FTA','FTP','ORB','DRB','TRB','AST','STL','BLK','TOV','PF','PTS','GmSc','MP','GAME_DATE']]
        df = df.applymap(str) #change everything to a string to load into buffer tables smoothly
        
        #prepare datatype for SQL insertion 
        dtyp = {c:types.VARCHAR(df[c].str.len().max())
                for c in df.columns[df.dtypes == 'object'].tolist()}
                
        #perform SQL insertion
        try: 
            date = url.replace('https://www.basketball-reference.com/friv/dailyleaders.fcgi?month=','').replace('&day=','/').replace('&year=','/')
            df.to_sql('nba_buffer_gamelog', engine, index=False, if_exists='append',dtype = dtyp, chunksize = 100)
            print(date)
        except BaseException as e:
            print('Failed to write to Oracle: '+ str(e))
        oracle_cur.close()
        oracle_con.close()
    except BaseException as e:
        fail_date = url.replace('https://www.basketball-reference.com/friv/dailyleaders.fcgi?month=','').replace('&day=','/').replace('&year=','/')
        print('Fail on date ' + fail_date + ': '+ str(e))
                

        
        
