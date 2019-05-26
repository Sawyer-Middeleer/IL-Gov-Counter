import pandas as pd
from sodapy import Socrata
import geopandas as gpd
import matplotlib.pyplot as plt
import requests

"""
1) Read tax rate & assessment ratio datasets
2) Read taxing body geographies
3) Join tax rate datasets to geographies
"""



"""
Read in those big ugly tax rate datasets and combine them into one big dataset with
tax rates from 2006 to 2016
"""
f1 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Tax Rates by Body 2006 - 2013.csv"
f2 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\TaxcodeAgencyFile2014.csv"
f3 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\TaxCodeAgencyFile2015.csv"
f4 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\TaxCodeAgencyRate2016.csv"
f5 = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\TaxCodeAgencyRate2017.csv"
files = [f1, f2, f3, f4, f5]
datasets = []

for f in files:
    df = pd.read_csv(f)
    datasets.append(df)
rates = pd.concat(datasets, ignore_index=True)

"""
Load in cook county assessment ratios dataset
"""
ratios = pd.read_csv(r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Cook County Assessment Ratios.csv")



"""
County Geography   *** ask Jeremy for this one
"""
#cty = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\ccgisdata - Political Township 2016.geojson"
#counties = gpd.read_file(cty)
"""
Townships Geography
"""
twn = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\ccgisdata - Political Township 2016.geojson"
townships = gpd.read_file(twn)
"""
Municipalities Geography
"""
mun = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\ccgisdata - Municipality 2014.geojson"
municipalities = gpd.read_file(mun)
"""
MWRD Geography
"""
mwrd = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\ccgisdata - Municipality 2014.geojson"
mwrd = gpd.read_file(mwrd)
"""
Elementary Schools Geography
"""
ele = r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\ccgisdata - Elementary School Tax District 2016.geojson"
elementary_schools = gpd.read_file(ele)
