import pandas as pd
from sodapy import Socrata
import numpy as np
import statsmodels.api as sm
import requests
import json
import csv
import re


params = {'2014_data' : "https://www.cookcountyclerk.com/file/7793",
#          '2015_data' : "https://www.cookcountyclerk.com/file/7794",
#          '2016_data' : "https://www.cookcountyclerk.com/file/7795",
          '2017_data' : "https://www.cookcountyclerk.com/file/8693",
          'file_path' :   r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\Cook County Assessment Ratios.csv",
          'export_path' : r'C:\Users\midde\OneDrive\Documents\GitHub\\IL-Gov-Counter'}

class CookCountyPropertyTax():

    def __init__(self, params):
        self.tax_2014 = params['2014_data']
#        self.tax_2015 = params['2015_data']
#        self.tax_2016 = params['2016_data']
        self.tax_2017 = params['2017_data']
        self.file_path = params['file_path']
        self.export_path = params['export_path']
        self.tax_rates = 'do'
        self.ratios_and_levels = 're'
        self.merged_tax_data = 'mi'
        self.cleaned_tax_data = 'fa'
        self.tax_rates_full = 'so'
    # """
    # --------------------------------------------------------------------------------
    # Read in tax rate datasets and combine them into one big dataset with
    # tax rates from 2006 to 2017
    # --------------------------------------------------------------------------------
    # """
    def read_write_tax_rates(self):
        dfs = []

        tax_df_2014 = pd.read_excel(self.tax_2014).rename(index=str, columns={'Taxcode':'Tax code', 'AgencyRate':'Agency Rate', 'TaxcodeRate':'Tax code Rate'})
        tax_df_2014['Tax Year'] = 2014
        # tax_df_2015 = pd.read_excel(self.tax_2015).rename(index=str, columns={'Taxcode':'Tax code', 'AgencyRate':'Agency Rate', 'TaxcodeRate':'Tax code Rate'})
        # tax_df_2015['Tax Year'] = 2015
        # tax_df_2016 = pd.read_excel(self.tax_2016).rename(index=str, columns={'TaxCode':'Tax code', 'AgencyRate':'Agency Rate', 'TaxcodeRate':'Tax code Rate'})
        # tax_df_2016['Tax Year'] = 2016
        tax_df_2017 = pd.read_excel(self.tax_2017).rename(index=str, columns={'TaxCode':'Tax code', 'AgencyRate':'Agency Rate', 'TaxcodeRate':'Tax code Rate'})
        tax_df_2017['Tax Year'] = 2017
        for df in [tax_df_2014, tax_df_2017]:
            dfs.append(df)

        # Join tax rate data into one Pandas dataframe
        tax_rates = pd.concat(dfs, ignore_index=True)
        # remove duplicate rows (there were some duplicates in 2006-7)
        tax_rates = tax_rates.drop_duplicates()
        tax_rates = tax_rates.sort_values(by='Tax Year', ascending=True)
        # Remove triple and double spaces from Agency Name column
        tax_rates['Agency Name'] = tax_rates['Agency Name'].map(lambda c: c.replace("   ", " "))
        tax_rates['Agency Name'] = tax_rates['Agency Name'].map(lambda c: c.replace("  ", " "))

        self.tax_rates = tax_rates

    # """
    # --------------------------------------------------------------------------------
    # Load in assessment district median assessment levels cook county assessment ratios dataset
    #
    # *** This data needs to be read in through a local file path because I had to copy it
    #     manually from PDFs, which can be found on the Illinois Department of Revenue's website.
    #     -- ex: http://www.revenue.state.il.us/AboutIdor/TaxStats/PropertyTaxStats/Table-1/2014-AssessmentRatios.pdf
    # --------------------------------------------------------------------------------
    # """
    def read_ratios_med_levels(self):
        ratios_and_median_levels = pd.read_csv(self.file_path)
        self.ratios_and_levels = ratios_and_median_levels

    # """
    # --------------------------------------------------------------------------------
    # Merge tax_rates and ratios_and_median_levels dfs
    # --------------------------------------------------------------------------------
    # """
    def merge_data(self, df1, df2):

        tax_rates = df1
        ratios_and_median_levels = df2
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

        # DO THE MERGE
        # merge tax_rates and ratios_and_median_levels dfs
        tax_rates_with_ratios = tax_rates.merge(ratios_and_median_levels, on=['Assessment District', 'Tax Year'], how='left', copy=False)
        self.merged_tax_data = tax_rates_with_ratios

    # """
    # --------------------------------------------------------------------------------
    # I want the agency name strings to look as nice as possible because
    # I'm a perfectionist/masochist or something
    # --------------------------------------------------------------------------------
    # """
    def clean_data(self, df):
        merged_tax_data = df
        # Fix text case
        merged_tax_data['Agency Name'] = merged_tax_data['Agency Name'].map(lambda c: c.title())

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
                          'Chgo' : 'Chicago',
                          'Metro ' : 'Metropolitan ',
                          'Mosq ' : 'Mosquito ',
                          'Tif ' : 'TIF ',
                          'Coll ' : 'College ',
                          'H S ' : 'High School',
                          'Twnshp ' : 'Township ',
                          'Spec ' : 'Special '}

        # This function will use the strings_to_fix dictionary to fix Agency Names all at once
        def fix_the_strings(df, dict):
            for key in dict:
                # replace key with value
                df['Agency Name'] = df['Agency Name'].map(lambda c: c.replace(key, dict[key]))
            return df

        fix_the_strings(merged_tax_data, strings_to_fix)

        self.cleaned_tax_data = merged_tax_data


    # """
    # --------------------------------------------------------------------------------
    # Now, calculate a new column for each tax code's 'effective property tax rate', which
    # tells you what percentage of a property’s value is taxed based on its equalized assessed value
    #
    # The effective property tax rate allows for an apples to apples comparison of tax rates across municipalities
    # and between different tax codes within municipalities.
    #
    # Function that calculates a new effective property tax rate column for a city using the Civic Federation's methodology:
    # https://www.civicfed.org/civic-federation/blog/calculate-your-communitys-effective-property-tax-rate
    #
    # Effective property tax rate = median level of assessment * county equalization factor * composite tax rate * 100
    #
    #
    # Add a second new column for each taxing body's proportion of the overall tax rate
    # --------------------------------------------------------------------------------
    # """
    def calculate_new_vars(self, df):
        tax_rates_with_ratios = df
        # Function to calculate effective property tax rate
        def calculate_eptr(df):
            df['Effective Property Tax Rate'] = df['Tax code Rate'] * 0.01 * df['Assessment Ratio'] * 0.01 * df['Cook County Equalization Factor'] * 100
            return df

        # Function to calculate each taxing body's proportion of the overall tax rate
        def calculate_rate_proportion(df):
            df['Tax Rate Proportion'] = df['Agency Rate'] / df['Tax code Rate']
            return df

        calculate_eptr(tax_rates_with_ratios)
        calculate_rate_proportion(tax_rates_with_ratios)
        # Calculate each taxing body's share of the effective property tax rate
        tax_rates_with_ratios['ETR Share'] = tax_rates_with_ratios['Tax Rate Proportion'] * tax_rates_with_ratios['Effective Property Tax Rate']
        tax_rates_full = tax_rates_with_ratios

        tax_rates_full.to_csv('tax_rates_full.csv', sep=',')
        self.tax_rates_full = tax_rates_full


    def categorize_agencies(self, df):
        tax_rates_full_nona = df.dropna()

        # print summary stats
        rate_stats_by_year = tax_rates_full_nona.groupby('Tax Year')['Effective Property Tax Rate'].describe().round(decimals=2)
        rate_stats_by_year['Tax Year'] = rate_stats_by_year.index

        # Explore tax rate agency composition over time
        def categorize_agency(s):
            words = s.split()
            if 'School' in words:
                return 'School'
            elif 'College' in words:
                return 'Community College'
            elif 'Park' in words:
                return 'Park and Forest'
            elif 'Forest' in words:
                return 'Park and Forest'
            elif 'Health' in words:
                return 'Public Health'
            elif 'Mosquito' in words:
                return 'Public Health'
            elif 'Sanitarium' in words:
                return 'Public Health'
            elif 'Cook' in words:
                return 'County'
            elif 'Village' in words and not ('Library' in words or 'School' in words or 'College' in words or 'Health' in words or 'Fire' in words or 'Special' in words or 'District' in words):
                return 'Municipality'
            elif 'City' in words and not ('Library' in words or 'School' in words or 'College' in words or 'Health' in words or 'Fire' in words or 'Special' in words or 'District' in words):
                return 'Municipality'
            elif 'Town' in words and not ('Library' in words or 'School' in words or 'College' in words or 'Health' in words or 'Fire' in words or 'Special' in words or 'District' in words):
                return 'Township'
            elif 'Library' in words:
                return 'Library'
            elif 'Fire' in words:
                return 'Fire Protection'
            else:
                return 'Other'

        tax_rates_full_nona['Agency Type'] = tax_rates_full_nona['Agency Name'].map(lambda c: categorize_agency(c))
        self.tax_rates_full = tax_rates_full_nona


    # """
    # Read dfs to csv, output figures
    # """
    def run_analysis(self):
        self.read_write_tax_rates()
        self.read_ratios_med_levels()
        self.merge_data(self.tax_rates, self.ratios_and_levels)
        self.clean_data(self.merged_tax_data)
        self.calculate_new_vars(self.cleaned_tax_data)
        self.categorize_agencies(self.tax_rates_full)


# Run the code
Taxes = CookCountyPropertyTax(params)
Taxes.run_analysis()

rates_df = Taxes.tax_rates_full
etr_shares = rates_df.groupby(['Tax Year', 'Tax code', 'Agency Type']).sum()['ETR Share']
etr_shares['Tax Year'] = etr_shares.index.levels[0]

rates_df = rates_df.merge(etr_shares, on=['Tax code', 'Tax Year', 'Agency Type'], how='left', copy=False)
rates_df = rates_df.rename(columns={'ETR Share_x':'ETR Share', 'ETR Share_y':'Agency Type ETR'})

rates_df.to_csv(Taxes.export_path+r'\tax_rates_full.csv', sep=',')
