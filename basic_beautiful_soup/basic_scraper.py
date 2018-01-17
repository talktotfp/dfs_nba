# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 17:47:30 2018

@author: tpauley
"""

import bs4
import requests
import pandas as pd

url = 'https://www.basketball-reference.com/friv/last_n_days.cgi?n=1'
tableHead = 'thead'
tableHeadRow = 'tr'
tableHeadCell = 'th'
tableBody = 'tbody'
tableBodyRow = 'tr'
tableBodyCell = 'td'

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
        df = pd.DataFrame(rowList, columns=headerList)
        return df


header = table_scrape('header',url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell)
body = table_scrape('df',url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell)

print(body)