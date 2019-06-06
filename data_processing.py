import pandas as pd
from sodapy import Socrata
import geopandas as gpd
import matplotlib.pyplot as plt
import requests
import json
import csv

"""
--------------------------------------------------------------------------------
to do:

-- Read tax rate & assessment ratio datasets [DONE]
-- Read taxing body geographies [DONE]
-- Clean tax rate data [DONE]
-- Try out Assessor web form scraping idea [DONE]
-- Figure out how to scrape using my own PIN inputs
-- Figure out how to scrape using address inputs
-- Clean geographic dataframes
-- Find remaining geographies
-- Subset tax rate dataframes according to taxing body type
-- Match tax rate data and geographic dataframes
-- Join tax rate & assessment ratio dataframes
-- Join tax rate datasets to geographies
-- Move into Ruby to query geographic datasets using address input

--------------------------------------------------------------------------------
"""

"""
--------------------------------------------------------------------------------
Function that calculates a new effective property tax rate column for a city using the Civic Federation's methodology:
https://www.civicfed.org/civic-federation/blog/calculate-your-communitys-effective-property-tax-rate

Effective property tax rate = median level of assessment * county equalization factor * composite tax rate * 100
--------------------------------------------------------------------------------
"""

"""
--------------------------------------------------------------------------------
Read in those big ugly tax rate datasets and combine them into one big dataset with
tax rates from 2006 to 2016
--------------------------------------------------------------------------------
"""
f1 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\Tax Rates by Body 2006 - 2013.csv"
f2 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\TaxcodeAgencyFile2014.csv"
f3 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\TaxCodeAgencyFile2015.csv"
f4 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\TaxCodeAgencyRate2016.csv"
f5 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\TaxCodeAgencyRate2017.csv"
files = [f1, f2, f3, f4, f5]
datasets = []

"""
--------------------------------------------------------------------------------
Load in assessment district median assessment levels cook county assessment ratios dataset
--------------------------------------------------------------------------------
"""
ratios_and_median_levels = pd.read_csv(r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\Cook County Assessment Ratios.csv")


"""
--------------------------------------------------------------------------------
Clean tax rate data
--------------------------------------------------------------------------------
"""

# Join tax rate data into one Pandas dataframe
for f in files:
    df = pd.read_csv(f)
    datasets.append(df)
tax_rates = pd.concat(datasets, ignore_index=True)

# remove duplicate rows (there were some duplicates in 2006-7)
tax_rates = tax_rates.drop_duplicates()
tax_rates = tax_rates.sort_values(by='Tax Year', ascending=True)


# Remove triple and double spaces from Agency Name column
tax_rates['Agency Name'] = tax_rates['Agency Name'].map(lambda c: c.replace("   ", " "))
tax_rates['Agency Name'] = tax_rates['Agency Name'].map(lambda c: c.replace("  ", " "))

# Create assessment districts column from townships
townships_list = tax_rates.loc[tax_rates['Agency Name'].str.contains('TOWN ') &
                                         ~tax_rates['Agency Name'].str.contains(' DIST') &
                                         ~tax_rates['Agency Name'].str.contains('FUND') &
                                         ~tax_rates['Agency Name'].str.contains('TIF') &
                                         ~tax_rates['Agency Name'].str.contains('SERVICE')]['Agency Name'].unique()

is_assessment_district = tax_rates['Agency Name'].map(lambda c: c in townships_list)

# create a temporary df of only rows that have agencies that are also assessment districts
df_to_merge = tax_rates[['Tax Year', 'Tax code','Agency Name']][is_assessment_district]

df_to_merge = df_to_merge.rename(columns={'Agency Name':'Assessment District'})
df_to_merge = df_to_merge.drop_duplicates()

tax_rates = tax_rates.merge(df_to_merge, on=['Tax code', 'Tax Year'], how='left', copy=False)

# Create column with count of taxing bodies in tax code
tax_rates['Taxing Body Count'] = tax_rates.groupby(['Tax Year', 'Tax code'])['Tax code'].transform('size')

def titlena(s):
    if type(s) == str:
        return s.title()

def remove_with_na(s, s2):
    if type(s) == str:
        return s.replace(s2, "")

# clean assessment district column
tax_rates['Assessment District'] = tax_rates['Assessment District'].map(lambda c: titlena(c))
tax_rates['Assessment District'] = tax_rates['Assessment District'].map(lambda c: remove_with_na(c, "Town Of "))
tax_rates['Assessment District'] = tax_rates['Assessment District'].map(lambda c: remove_with_na(c, "Town "))
tax_rates.head()

# merge tax_rates and ratios_and_median_levels dfs
# do some data cleaning first
ratios_and_median_levels = ratios_and_median_levels.rename(columns={'Year':'Tax Year'})
ratios_and_median_levels['Assessment District'] = ratios_and_median_levels['Assessment District'].map(lambda c: c.replace("Norwood park", "Norwood Park"))
ratios_and_median_levels.loc[ratios_and_median_levels['Assessment District']=='Calumet'] # some years calumet didn't have a number
# get rid of rows with NaN assessment districts (figure this out later)
tax_rates = tax_rates.dropna()
tax_rates_with_ratios = tax_rates.merge(ratios_and_median_levels, on=['Assessment District', 'Tax Year'], how='left', copy=False)
tax_rates_with_ratios = tax_rates_with_ratios.dropna()
# read dfs to csv file
#tax_rates.to_csv('tax_rates.csv', sep=',')
tax_rates_with_ratios.to_csv('tax_rates_with_ratios.csv', sep=',')


"""
--------------------------------------------------------------------------------
Let's do some web scraping!

This particular script only works for PIN inputs. If I want to let users query
using address data, I could use cc gis address points data to convert
--------------------------------------------------------------------------------
"""

from urllib.request import urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup

pin = '33074170350000'
html = urlopen('http://www.cookcountyassessor.com/Property.aspx?mode=details&pin='+pin)
bsObj = BeautifulSoup(html.read())
tax_code = bsObj.find(id="ctl00_phArticle_ctlPropertyDetails_lblPropInfoTaxcode")
print("Tax code: " + tax_code.get_text())

"""
--------------------------------------------------------------------------------
Test out using the scraped tax code

Use tax code to find taxing bodies for specific tax codes
--------------------------------------------------------------------------------
"""

filtered_rates = tax_rates.loc[tax_rates['Tax code'] == int(tax_code.get_text())]
filtered_rates.loc[filtered_rates['Tax Year'] == 2017]



"""
--------------------------------------------------------------------------------
Explore trends in the data
--------------------------------------------------------------------------------
"""

rates_2017 = tax_rates.loc[tax_rates['Tax Year'] == 2017]
rates_2017.groupby('Tax code').Agency.nunique().mean()

tax_rates.groupby(['Tax Year','Tax code'])['Agency'].nunique()
