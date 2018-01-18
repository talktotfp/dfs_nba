# -*- coding: utf-8 -*-
"""
Created on Wed Jan 17 17:47:30 2018

Author: Tyler Pauley
Description: Generic table scraper that uses URL and HTML parameters as inputs. Most web pages will require tweaks.
"""

import bs4 #beautifulSoup web scraper
import requests #for HTTP requests
import pandas as pd #for building dataframe

#==============================================================================
#Function Parameters
#returnType: 'head' for a list of column headers, 'body' for a list of data arrays, 'df' for a dataframe of table
#url: web address to be scraped
#tableHead/Row/Cell: html object types (i.e. 'thead,'tr','td',etc) for the table header 
#tableBody/Row/Cell: html object types (i.e. 'thead,'tr','td',etc) for the table data 
#==============================================================================


def table_scrape(returnType,url,tableHead,tableHeadRow,tableHeadCell,tableBody,tableBodyRow,tableBodyCell):
    
    response = requests.get(url) #send HTTP request to url
    soup = bs4.BeautifulSoup(response.text,"lxml") #get entire webpage contents

#==============================================================================
#Headers
    
    head = soup.find(tableHead) #search for header (1st) as defined in tableHead parameter
    headers = head.find(tableHeadRow).find_all(tableHeadCell) #find all rows and cells within that header
    headerList = [] #create an empty list
    for iHeaders in headers: #iterate through cells of the header
        headerList.append(iHeaders.string)  #append cell contents as strings into list

#==============================================================================
#Body/Data
        
    body = soup.find(tableBody) #search for table body (1st) as defined in tableHead parameter
    rows = body.find_all(tableBodyRow) #find all rows contained within that body
    rowList = [] #create an empty list to store further lists of data (i.e. lists inside a list)
    for iRows in rows: #iterate over the rows in the table body
        cellList = [] #create a temporary empty list to contain the cell contents of an individual row
        for iCell in iRows: #iterate over each cell in a row
            cellList.append(iCell.string) #append the cell contents (as a string) to the temporary list
        rowList.append(cellList) #append the temporary list into the main row list
        
#==============================================================================
#Returning Data
      
    if len(headers) != len(rowList[0]): #provide warning if number of columns in header doesn't match body
        print('Warning: Number of columns in header (' + str(len(headers)) + ') does not match body(' + str(len(rowList[0])) + ')')
    if returnType == 'header':
        return headerList
    if returnType == 'body':
        return rowList
    if returnType == 'df' and len(headers) == len(rowList[0]):
        df = pd.DataFrame(data = rowList[0]).T
        df.columns = headerList
        return df
        
