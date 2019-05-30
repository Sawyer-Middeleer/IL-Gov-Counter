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


# Join tax rate data into one Pandas dataframe
for f in files:
    df = pd.read_csv(f)
    datasets.append(df)
tax_rates = pd.concat(datasets, ignore_index=True)

"""
--------------------------------------------------------------------------------
Load in assessment district median assessment levels cook county assessment ratios dataset
--------------------------------------------------------------------------------
"""
ratios_and_median_levels = pd.read_csv(r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\Cook County Assessment Ratios.csv")


"""
--------------------------------------------------------------------------------
Read in Political Boundary GeoJSONs

*** NEED TO FIND/ASK FOR
--- County, consolidated elections, forest preserve, general assistance,
    road and bridge, mental health, public health, special service areas, mosquito abatement
--------------------------------------------------------------------------------
"""
# County Geography   *** ask Jeremy for this one
#cty = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\ccgisdata - Political Township 2016.geojson"
#counties = gpd.read_file(cty)

# Townships Geography
twn = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Political Township 2016.geojson"
townships = gpd.read_file(twn)
townships.sort_values(['name'])

# Municipalities Geography
mun = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Municipality 2014.geojson"
municipalities = gpd.read_file(mun)

# MWRD Geography
mwr = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Metropolitan Water Reclamation Tax Dist 2015.geojson"
mwrd = gpd.read_file(mwr)

# Elementary Schools Geography
ele = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Elementary School Tax District 2016.geojson"
elementary_schools = gpd.read_file(ele)

# High School Geography
hgh = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - High School Tax Dist 2015.geojson"
high_schools = gpd.read_file(hgh)

# Community College Geography
com = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Community College Tax District 2016.geojson"
community_colleges = gpd.read_file(com)

# Unit School Geography
unt = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Unit School Tax Districts 2015.geojson"
unit_schools = gpd.read_file(unt)

# Library District Geography
lib = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Library Tax Dist 2015.geojson"
libraries = gpd.read_file(lib)

# Park District Geography
prk = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Park Tax Dist 2015.geojson"
parks = gpd.read_file(prk)

# Sanitary District Geography
san = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Sanitary Tax Dist 2015.geojson"
sanitary_districts = gpd.read_file(san)

# Fire Protection District Geography
fir = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Fire Protection Tax Dist 2016.geojson"
fire_protection_districts = gpd.read_file(fir)

#TIF Districts
tif = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\ccgisdata - Tax Increment Financing (TIF) Districts 2016.geojson"
tif_districts = gpd.read_file(tif)

"""
--------------------------------------------------------------------------------
Clean tax rate data
--------------------------------------------------------------------------------
"""
# Remove triple and double spaces from Agency Name column
rates['Agency Name'] = rates['Agency Name'].map(lambda c: c.replace("   ", " "))
rates['Agency Name'] = rates['Agency Name'].map(lambda c: c.replace("  ", " "))



# If you can query the cook county asseessor database with an address, then you can scrape the tax code
# If you have the tax code, then you can find all of the relevant taxing districts WITHOUT shapefiles

len(rates['Tax code'].unique()) #3968 unique tax codes

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

Use tax code to find taxing bodies
--------------------------------------------------------------------------------
"""
