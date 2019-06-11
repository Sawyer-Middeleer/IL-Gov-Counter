import pandas as pd
from sodapy import Socrata
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import statsmodels.api as sm
import requests
import json
import csv
import re


params = {'2006-2013_data' :  "https://datacatalog.cookcountyil.gov/api/views/9sqg-vznj/rows.csv?accessType=DOWNLOAD&bom=true&format=true",
          '2014_data' : "https://www.cookcountyclerk.com/file/7793",
          '2015_data' : "https://www.cookcountyclerk.com/file/7794",
          '2016_data' : "https://www.cookcountyclerk.com/file/7795",
          '2017_data' : "https://www.cookcountyclerk.com/file/8693",
          'file_path' :   r"C:\Users\midde\OneDrive\Documents\GitHub\IL-Gov-Counter\Data_Files\Cook County Assessment Ratios.csv",
          'export_path' : r'C:\Users\midde\OneDrive\Documents\GitHub\\IL-Gov-Counter'}

class CookCountyPropertyTax():

    def __init__(self, params):
        self.tax_2006_2013 = params['2006-2013_data']
        self.tax_2014 = params['2014_data']
        self.tax_2015 = params['2015_data']
        self.tax_2016 = params['2016_data']
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
        tax_df_2015 = pd.read_excel(self.tax_2015).rename(index=str, columns={'Taxcode':'Tax code', 'AgencyRate':'Agency Rate', 'TaxcodeRate':'Tax code Rate'})
        tax_df_2015['Tax Year'] = 2015
        tax_df_2016 = pd.read_excel(self.tax_2016).rename(index=str, columns={'TaxCode':'Tax code', 'AgencyRate':'Agency Rate', 'TaxcodeRate':'Tax code Rate'})
        tax_df_2016['Tax Year'] = 2016
        tax_df_2017 = pd.read_excel(self.tax_2017).rename(index=str, columns={'TaxCode':'Tax code', 'AgencyRate':'Agency Rate', 'TaxcodeRate':'Tax code Rate'})
        tax_df_2017['Tax Year'] = 2017
        for df in [tax_df_2014, tax_df_2015, tax_df_2016, tax_df_2017]:
            dfs.append(df)
        dfs.append(pd.read_csv(self.tax_2006_2013))

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


    # """
    # --------------------------------------------------------------------------------
    # Explore trends in the data
    #
    # To begin, first start by analyzing 2017 data
    # --------------------------------------------------------------------------------
    # """
    def exploratory_data_analysis(self, df):
        rates_2017 = df.loc[df['Tax Year'] == 2017]

        # drop duplicates and NA values
        rates_2017_unique_rates = rates_2017.drop_duplicates('Tax code').dropna()

        # print summary stats
        rates_2017_unique_rates['Effective Property Tax Rate'].describe().round(decimals=2)

        # histogram of number of taxing bodies
        n, bins, patches = plt.hist(rates_2017_unique_rates['Taxing Body Count'],
                                    bins=[8,9,10,11,12,13,14,15,16,17,18,19,20],
                                    facecolor='b',
                                    alpha=0.75,
                                    density=True,
                                    edgecolor='gray')
        plt.xlabel('Number of Taxing Bodies')
        plt.ylabel('Proportion')
        plt.title('Histogram of Taxing Body Count per Tax Code Group, 2017')
        plt.axis([8, 20, 0, 0.4])
        plt.savefig(self.export_path+r"\Hist_Taxing_Body_Count_Per_Code_2017.png")
        plt.show()

        # histogram of etr
        n, bins, patches = plt.hist(rates_2017_unique_rates['Effective Property Tax Rate'],
                                    bins='auto',
                                    facecolor='b',
                                    alpha=0.75,
                                    normed=1,
                                    edgecolor='gray')
        plt.xlabel('Effective Property Tax Rate')
        plt.ylabel('Proportion')
        plt.title('Histogram of Effective Property Tax Rates for Cook County Tax Codes, 2017')
        plt.axis([0, 12, 0, 0.6])
        plt.savefig(self.export_path+r"\Hist_ETR_By_Tax_Code_2017.png")
        plt.show()

        # Comparison of assessment districts by number of taxing bodies and effective tax rate
        assessment_dist_comps = rates_2017_unique_rates.groupby('Assessment District')['Taxing Body Count','Effective Property Tax Rate'].agg(['mean','std','min','max']).round(decimals=2)

        def least_squares_regression(df):
            # Do a linear regression with # bodies - ETR relationship
            model = sm.OLS(df['Effective Property Tax Rate']['mean'], df['Taxing Body Count']['mean'])
            results = model.fit()

            ols_text_file = open(self.export_path+r"\Output_OLS.txt", "w")
            ols_text_file.write(str(results.summary()))
            ols_text_file.close()

            print(results.summary())

            # Plot scatter plot with line of best fit
            # Thanks to this thread: https://stackoverflow.com/questions/22239691/code-for-best-fit-straight-line-of-a-scatter-plot-in-python
            plt.plot(df['Taxing Body Count']['mean'],
                     df['Effective Property Tax Rate']['mean'],
                     'bo')
            plt.plot(np.unique(df['Taxing Body Count']['mean']),
                     np.poly1d(np.polyfit(df['Taxing Body Count']['mean'],
                     df['Effective Property Tax Rate']['mean'], 1))(np.unique(df['Taxing Body Count']['mean'])))
            plt.axis([12.5,16,0,8])
            plt.title('Average Taxing Body Count vs Average ETR by Assessment District')
            plt.xlabel('Average Taxing Body Count for Tax Codes in Each Assessment District')
            plt.ylabel('Effective Property Tax Rate')
            plt.savefig(self.export_path+r"\Average_Taxing_Body_Count_vs_Average_ETR_by_Assessment_District.png")
            plt.show()

        least_squares_regression(assessment_dist_comps)

        # plot the above, but with standard deviation error bars
        plt.plot(assessment_dist_comps['Taxing Body Count']['mean'],
                 assessment_dist_comps['Effective Property Tax Rate']['mean'],
                 'ro')
        plt.errorbar(assessment_dist_comps['Taxing Body Count']['mean'],
                     assessment_dist_comps['Effective Property Tax Rate']['mean'],
                     assessment_dist_comps['Effective Property Tax Rate']['std'],
                     linestyle='None',
                     marker='^')
        plt.axis([12.5,16,0,8])
        plt.title('Average Taxing Body Count vs Average ETR by Assessment District (Error Bars Show One Standard Deviation)')
        plt.xlabel('Average Taxing Body Count for Tax Codes in Each Assessment District')
        plt.ylabel('Effective Property Tax Rate')
        plt.savefig(self.export_path+r"\Taxing_Body_Count_vs_Average_ETR_by_Assessment_District_With_Variance.png")
        plt.show()

        # looks like some of these points have really high variance... let's explore what's going on there
        high_var_districts = assessment_dist_comps.loc[assessment_dist_comps['Effective Property Tax Rate']['std'] > 1.0].index

        high_var_etr = rates_2017_unique_rates.loc[(rates_2017_unique_rates['Assessment District'] == high_var_districts[0]) |
                                                   (rates_2017_unique_rates['Assessment District'] == high_var_districts[1])|
                                                   (rates_2017_unique_rates['Assessment District'] == high_var_districts[2]) |
                                                   (rates_2017_unique_rates['Assessment District'] == high_var_districts[3]) |
                                                   (rates_2017_unique_rates['Assessment District'] == high_var_districts[4])]

        grouped_high_var = high_var_etr.groupby(['Assessment District', 'Tax code']).mean()[['Taxing Body Count', 'Effective Property Tax Rate']]
        ad_df = pd.DataFrame(grouped_high_var.index.levels[0])

        grouped_high_var = grouped_high_var.merge(ad_df, on=['Assessment District'], how='left', copy=False)

        bloom = grouped_high_var[grouped_high_var['Assessment District']=='Bloom']
        bremen = grouped_high_var[grouped_high_var['Assessment District']=='Bremen']
        calumet = grouped_high_var[grouped_high_var['Assessment District']=='Calumet']
        rich = grouped_high_var[grouped_high_var['Assessment District']=='Rich']
        thornton = grouped_high_var[grouped_high_var['Assessment District']=='Thornton']


        fig, ax = plt.subplots(2, 3, figsize=(15, 8))
        ax[0, 0].plot(bloom['Taxing Body Count'], bloom['Effective Property Tax Rate'], 'k.', alpha=0.6)
        ax[0, 0].set_title('Bloom')
        ax[0, 1].plot(bremen['Taxing Body Count'], bremen['Effective Property Tax Rate'], 'k.', alpha=0.6)
        ax[0, 1].set_title('Bremen')
        ax[0, 2].plot(calumet['Taxing Body Count'], calumet['Effective Property Tax Rate'], 'k.', alpha=0.6)
        ax[0, 2].set_title('Calumet')
        ax[1, 0].plot(rich['Taxing Body Count'], rich['Effective Property Tax Rate'], 'k.', alpha=0.6)
        ax[1, 0].set_title('Rich')
        ax[1, 1].plot(thornton['Taxing Body Count'], thornton['Effective Property Tax Rate'], 'k.', alpha=0.6)
        ax[1, 1].set_title('Thornton')
        sns.despine()
        fig.suptitle('Taxing Body Count vs ETR for each Tax Code by Assessment District, Tax Year 2017', fontsize=14)
        fig.text(0.5, 0.04, 'Taxing Body Count', ha='center', va='center', fontsize=12)
        fig.text(0.06, 0.5, 'Effective Property Tax Rate', ha='center', va='center', rotation='vertical', fontsize=12)
        for a in ax.flat:
            a.label_outer()
            a.grid(False)
        plt.savefig(self.export_path+r"\Taxing_Body_Count_ETR_by_Assessment_Dist_High_Variance_Only.png")
        plt.show()

    # """
    # Now explore trends over time
    #
    # In this analysis, I'll explore how different types of government units have been represented over time
    # """
    def historical_analysis(self, df):
        tax_rates_full_nona = df.dropna()

        # print summary stats
        rate_stats_by_year = tax_rates_full_nona.groupby('Tax Year')['Effective Property Tax Rate'].describe().round(decimals=2)
        rate_stats_by_year['Tax Year'] = rate_stats_by_year.index
        rate_stats_by_year
        # Average effective tax rate over time
        plt.plot(rate_stats_by_year['Tax Year'],
                 rate_stats_by_year['mean'],
                 'b--')
        plt.title('Average Cook County ETR 2006-2017')
        plt.xlabel('Year')
        plt.ylabel('Effective Property Tax Rate')
        plt.savefig(self.export_path+r"\Cook_County_ETR_06_17.png")
        plt.show()

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
            elif 'Village' in words and not ('Library' in words):
                return 'Municipality'
            elif 'City' in words and not ('Library' in words):
                return 'Municipality'
            elif 'Town' in words and not ('School' in words):
                return 'Township'
            elif 'Library' in words:
                return 'Library'
            elif 'Fire' in words:
                return 'Fire Protection'
            else:
                return 'Other'

        tax_rates_full_nona['Agency Type'] = tax_rates_full_nona['Agency Name'].map(lambda c: categorize_agency(c))
        self.tax_rates_full = tax_rates_full_nona
        unique_agencies = tax_rates_full_nona.drop_duplicates(['Agency', 'Tax Year'])
        grouped_unique_agencies = unique_agencies.groupby(['Tax Year', 'Agency Type']).count()

        y2006 = unique_agencies[unique_agencies['Tax Year']==2006].groupby('Agency Type').mean().sort_values('ETR Share')
        y2007 = unique_agencies[unique_agencies['Tax Year']==2007].groupby('Agency Type').mean().sort_values('ETR Share')
        y2008 = unique_agencies[unique_agencies['Tax Year']==2008].groupby('Agency Type').mean().sort_values('ETR Share')
        y2009 = unique_agencies[unique_agencies['Tax Year']==2009].groupby('Agency Type').mean().sort_values('ETR Share')
        y2010 = unique_agencies[unique_agencies['Tax Year']==2010].groupby('Agency Type').mean().sort_values('ETR Share')
        y2011 = unique_agencies[unique_agencies['Tax Year']==2011].groupby('Agency Type').mean().sort_values('ETR Share')
        y2012 = unique_agencies[unique_agencies['Tax Year']==2012].groupby('Agency Type').mean().sort_values('ETR Share')
        y2013 = unique_agencies[unique_agencies['Tax Year']==2013].groupby('Agency Type').mean().sort_values('ETR Share')
        y2014 = unique_agencies[unique_agencies['Tax Year']==2014].groupby('Agency Type').mean().sort_values('ETR Share')
        y2015 = unique_agencies[unique_agencies['Tax Year']==2015].groupby('Agency Type').mean().sort_values('ETR Share')
        y2016 = unique_agencies[unique_agencies['Tax Year']==2016].groupby('Agency Type').mean().sort_values('ETR Share')
        y2017 = unique_agencies[unique_agencies['Tax Year']==2017].groupby('Agency Type').mean().sort_values('ETR Share')

        y2006['Agency Type'] = y2006.index
        y2007['Agency Type'] = y2007.index
        y2008['Agency Type'] = y2008.index
        y2009['Agency Type'] = y2009.index
        y2010['Agency Type'] = y2010.index
        y2011['Agency Type'] = y2011.index
        y2012['Agency Type'] = y2012.index
        y2013['Agency Type'] = y2013.index
        y2014['Agency Type'] = y2014.index
        y2015['Agency Type'] = y2015.index
        y2016['Agency Type'] = y2016.index
        y2017['Agency Type'] = y2017.index

        def calculate_etr_change(df1, df2):
            df1['Y-o-Y ETR Change'] = (df1['ETR Share']-df2['ETR Share'])/df2['ETR Share']
            return df1

        calculate_etr_change(y2007, y2006)
        calculate_etr_change(y2008, y2007)
        calculate_etr_change(y2009, y2008)
        calculate_etr_change(y2010, y2009)
        calculate_etr_change(y2011, y2010)
        calculate_etr_change(y2012, y2011)
        calculate_etr_change(y2013, y2012)
        calculate_etr_change(y2014, y2013)
        calculate_etr_change(y2015, y2014)
        calculate_etr_change(y2016, y2015)
        calculate_etr_change(y2017, y2016)

        labels = ['Public Health', 'Other', 'Township', 'Community College', 'Library', 'Park and Forest',
                  'Municipality', 'Fire Protection', 'County', 'School']

        colors2 = ['red','blue','maroon','magenta','goldenrod','blue','green','gray','black','cyan','chocolate']

        fig, ax = plt.subplots(2, 6, figsize=(24,18))
        ax[0,0].bar(y2007['Agency Type'], y2007['Y-o-Y ETR Change'], color=colors2)
        ax[0,1].bar(y2008['Agency Type'], y2008['Y-o-Y ETR Change'], color=colors2)
        ax[0,2].bar(y2009['Agency Type'], y2009['Y-o-Y ETR Change'], color=colors2)
        ax[0,3].bar(y2010['Agency Type'], y2010['Y-o-Y ETR Change'], color=colors2)
        ax[0,4].bar(y2011['Agency Type'], y2011['Y-o-Y ETR Change'], color=colors2)
        ax[0,5].bar(y2012['Agency Type'], y2012['Y-o-Y ETR Change'], color=colors2)
        ax[1,0].bar(y2013['Agency Type'], y2013['Y-o-Y ETR Change'], color=colors2)
        ax[1,1].bar(y2014['Agency Type'], y2014['Y-o-Y ETR Change'], color=colors2)
        ax[1,2].bar(y2015['Agency Type'], y2015['Y-o-Y ETR Change'], color=colors2)
        ax[1,3].bar(y2016['Agency Type'], y2016['Y-o-Y ETR Change'], color=colors2)
        ax[1,4].bar(y2017['Agency Type'], y2017['Y-o-Y ETR Change'], color=colors2)
        ax[0,0].set_ybound(lower=-0.4, upper=.8)
        ax[0,0].set_title("2007")
        ax[0,1].set_ybound(lower=-0.4, upper=.8)
        ax[0,1].set_title("2008")
        ax[0,2].set_ybound(lower=-0.4, upper=.8)
        ax[0,2].set_title("2009")
        ax[0,3].set_ybound(lower=-0.4, upper=.8)
        ax[0,3].set_title("2010")
        ax[0,4].set_ybound(lower=-0.4, upper=.8)
        ax[0,4].set_title("2011")
        ax[0,5].set_ybound(lower=-0.4, upper=.8)
        ax[0,5].set_title("2012")
        ax[1,0].set_ybound(lower=-0.4, upper=.8)
        ax[1,0].set_title("2013")
        ax[1,1].set_ybound(lower=-0.4, upper=.8)
        ax[1,1].set_title("2014")
        ax[1,2].set_ybound(lower=-0.4, upper=.8)
        ax[1,2].set_title("2015")
        ax[1,3].set_ybound(lower=-0.4, upper=.8)
        ax[1,3].set_title("2016")
        ax[1,4].set_ybound(lower=-0.4, upper=.8)
        ax[1,4].set_title("2017")
        ax[1,5].set_ybound(lower=-0.4, upper=.8)
        ax[0,0].set_xticklabels(labels, rotation=60, ha='right')
        ax[0,1].set_xticklabels(labels, rotation=60, ha='right')
        ax[0,2].set_xticklabels(labels, rotation=60, ha='right')
        ax[0,3].set_xticklabels(labels, rotation=60, ha='right')
        ax[0,4].set_xticklabels(labels, rotation=60, ha='right')
        ax[0,5].set_xticklabels(labels, rotation=60, ha='right')
        ax[1,0].set_xticklabels(labels, rotation=60, ha='right')
        ax[1,1].set_xticklabels(labels, rotation=60, ha='right')
        ax[1,2].set_xticklabels(labels, rotation=60, ha='right')
        ax[1,3].set_xticklabels(labels, rotation=60, ha='right')
        ax[1,4].set_xticklabels(labels, rotation=60, ha='right')
        ax[1,5].set_xticklabels(labels, rotation=60, ha='right')
        fig.suptitle('Year-over-Year Effective Tax Rate Change by Agency Type, 2007-2017', fontsize=18)
        fig.text(0.5, 0.04, 'Taxing Body Category', ha='center', va='center', fontsize=14)
        fig.text(0.06, 0.5, 'Proportional ETR Change', ha='center', va='center', rotation='vertical', fontsize=14)
        plt.savefig(self.export_path+r"\ETR_Share_By_Agency_Type_06_17.png")
        plt.show()

    # """
    # Read dfs to csv, output figures
    # """
    def run_analysis(self):
        self.read_write_tax_rates()
        self.tax_rates.to_csv(self.export_path+r'\tax_rates.csv', sep=',')

        self.read_ratios_med_levels()
        self.ratios_and_levels.to_csv(self.export_path+r'\ratios_and_levels.csv', sep=',')

        self.merge_data(self.tax_rates, self.ratios_and_levels)
        self.merged_tax_data.to_csv(self.export_path+r'\merged_tax_data.csv', sep=',')

        self.clean_data(self.merged_tax_data)
        self.cleaned_tax_data.to_csv(self.export_path+r'\cleaned_tax_data.csv', sep=',')

        self.calculate_new_vars(self.cleaned_tax_data)

        self.tax_rates_full.to_csv(self.export_path+r'\tax_rates_full.csv', sep=',')

# Run the code
Taxes = CookCountyPropertyTax(params)
Taxes.run_analysis()
