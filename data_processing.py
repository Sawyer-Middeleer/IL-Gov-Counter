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

-- Put all this shit in classes and methods
-- Read tax rate & assessment ratio datasets [DONE]
-- Read taxing body geographies [DONE]
-- Clean tax rate data [DONE]
-- Try out Assessor web form scraping idea [DONE]
-- Figure out how to scrape using my own PIN inputs [DONE]
-- Figure out how to scrape using address inputs
-- Subset tax rate dataframes according to taxing body type
-- Join tax rate & assessment ratio dataframes [DONE]

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
Prepare data for analysis
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

"""
--------------------------------------------------------------------------------
Merge tax_rates and ratios_and_median_levels dfs
--------------------------------------------------------------------------------
"""

# Create assessment districts column from townships

# First, create a list of townships by filtering out the tax_rates Agency Name column
townships_list = tax_rates.loc[tax_rates['Agency Name'].str.contains('TOWN ') &
                                         ~tax_rates['Agency Name'].str.contains(' DIST') &
                                         ~tax_rates['Agency Name'].str.contains('FUND') &
                                         ~tax_rates['Agency Name'].str.contains('TIF') &
                                         ~tax_rates['Agency Name'].str.contains('SERVICE')]['Agency Name'].unique()

# Make a big list, length equal to the length of tax_rates, indicating which row's agencies are also assessment district names
# There will be at most one assessment district per tax code group
is_assessment_district = tax_rates['Agency Name'].map(lambda c: c in townships_list)

# create a temporary df of only rows that have agencies that are also assessment districts, with some other variables
df_to_merge = tax_rates[['Tax Year', 'Tax code','Agency Name']][is_assessment_district]

# Rename Agency Name Column to Assessment District and drop duplicate rows,
# which came from there being multiple years of nearly identical data
df_to_merge = df_to_merge.rename(columns={'Agency Name':'Assessment District'})
df_to_merge = df_to_merge.drop_duplicates()

# Merge the temporary df with the tax_rates df to add Assessment District column
tax_rates = tax_rates.merge(df_to_merge, on=['Tax code', 'Tax Year'], how='left', copy=False)

# Create column with count of taxing bodies in each tax code group
tax_rates['Taxing Body Count'] = tax_rates.groupby(['Tax Year', 'Tax code'])['Tax code'].transform('size')

# do some data cleaning so that the merge will work properly

# str.title() and replace() break if there are NA values, so I wrote a couple helper functions
def titlena(s):
    if type(s) == str:
        return s.title()

def remove_with_na(s, s2):
    if type(s) == str:
        return s.replace(s2, "")

# Clean strings and column names to match up naming conventions first
tax_rates['Assessment District'] = tax_rates['Assessment District'].map(lambda c: titlena(c))
tax_rates['Assessment District'] = tax_rates['Assessment District'].map(lambda c: remove_with_na(c, "Town Of "))
tax_rates['Assessment District'] = tax_rates['Assessment District'].map(lambda c: remove_with_na(c, "Town "))
ratios_and_median_levels = ratios_and_median_levels.rename(columns={'Year':'Tax Year'})
ratios_and_median_levels['Assessment District'] = ratios_and_median_levels['Assessment District'].map(lambda c: c.replace("Norwood park", "Norwood Park"))

# DO THE MERGE!
# merge tax_rates and ratios_and_median_levels dfs
tax_rates_with_ratios = tax_rates.merge(ratios_and_median_levels, on=['Assessment District', 'Tax Year'], how='left', copy=False)

# Getting there....
tax_rates_with_ratios.head()

"""
--------------------------------------------------------------------------------
I want the agency name strings to look as nice as possible because
I'm a perfectionist/fucking masochist or something
--------------------------------------------------------------------------------
"""
# Fix text case
tax_rates_with_ratios['Agency Name'] = tax_rates_with_ratios['Agency Name'].map(lambda c: c.title())

# Rather than writing a thousand lines with the map method,
# I'm going to make a dictionary of everything I need to fix and then write a function to do it all at once.

strings_to_fix = {'County Of Cook' : 'Cook County',
                  'Of' : 'of',
                  'Ssa' : 'SSA',
                  'Vil ' : 'Village ',
                  'Dist ' : 'District ',
                  'Distr ' : 'District ',
                  'Lib ' : 'Library ',
                  'T B ' : 'Tuberculosis ',
                  'Gr ' : 'Greater ',
                  'Hts ' : 'Heights ',
                  'Sch ' : 'School ',
                  'Comm ' : 'Community ',
                  'C C ' : 'Community Consolidated ',
                  'Hlth ' : 'Health ',
                  'Spec Serv' : 'Special Service',
                  'Fac&serv ' : 'Facility & Service ',
                  'Twp ' : 'Township ',
                  'Pub ' : 'Public ',
                  'Metro ' : 'Metropolitan ',
                  'Mosq ' : 'Mosquito ',
                  'Tif ' : 'TIF ',
                  'Coll ' : 'College ',
                  'H S ' : 'High School',
                  'Twnshp ' : 'Township ',
                  'Spec ' : 'Special '}

# This function will use the strings_to_fix dictionary to fix Agency Names all at once
def fix_the_goddamn_strings(df, dict):
    for key in dict:
        # replace key with value
        df['Agency Name'] = df['Agency Name'].map(lambda c: c.replace(key, dict[key]))
    return df

fix_the_goddamn_strings(tax_rates_with_ratios, strings_to_fix)


"""
--------------------------------------------------------------------------------
Now, calculate a new column for each tax code's 'effective property tax rate'
and a second new column for each taxing body's proportion of the overall tax rate

Function that calculates a new effective property tax rate column for a city using the Civic Federation's methodology:
https://www.civicfed.org/civic-federation/blog/calculate-your-communitys-effective-property-tax-rate

Effective property tax rate = median level of assessment * county equalization factor * composite tax rate * 100
--------------------------------------------------------------------------------
"""

def calculate_eptr(df):
    df['Effective Property Tax Rate'] = df['Tax code Rate'] * 0.01 * df['Assessment Ratio'] * 0.01 * df['Cook County Equalization Factor'] * 100
    return df

def calculate_rate_proportion(df):
    df['Tax Rate Proportion'] = df['Agency Rate'] / df['Tax code Rate']
    return df

calculate_eptr(tax_rates_with_ratios)
calculate_rate_proportion(tax_rates_with_ratios)

tax_rates_full = tax_rates_with_ratios

tax_rates_full.head()

tax_rates_full.loc[(tax_rates_full['Assessment District'] == 'Oak Park') &
                   (tax_rates_full['Tax Year'] == 2017) &
                   (tax_rates_full['Tax code'] == 27002)].sort_values(by='Agency Rate', ascending=False)


"""
--------------------------------------------------------------------------------
Explore trends in the data
--------------------------------------------------------------------------------
"""

rates_2017 = tax_rates.loc[tax_rates['Tax Year'] == 2017]
rates_2017.groupby('Tax code').Agency.nunique().mean()

tax_rates.groupby(['Tax Year','Tax code'])['Agency'].nunique()

"""
Do some mapping if I have time
"""


"""
Read to CSV
"""
#tax_rates_with_ratios = tax_rates_with_ratios.dropna()
#tax_rates_with_ratios.to_csv('tax_rates_with_ratios.csv', sep=',')
