"""
********************************************************************************
                    Sero Interview Task Code Package
********************************************************************************
This package contains the functions created to complete the Sero interview task.
Python packages required for this code are listed in the
accompanying requirements.txt file. Most of those packages should be general
everyday Python packages, with the exception of fpdf (a package that is used to
output a .pdf report). No worries if you want to avoid installing that, it is
only used in the make_landlord_report function, and everything used in that
function can be accessed seperately in the earlier functions!
For this I have just focused on some simple visualisations, and then a simple
analysis of which properties the landlord should focus on (based on their goal,
i.e. cost savings or emissions), and then some simple recommendations, which gets
output into a report for the landlord.

Functions & classes included within this package:
    - clean_epc_data
    - view_portfolio_map
    - get_potential_cost_saved
    - get_co2_emissions_potential_difference
    - get_features
    - plot_scatter
    - property_focus_feature_analysis
    - get_recommendations
    - make_cost_savings_report

AUTHOR:
    Tania LaGambina
********************************************************************************
"""
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import os
from urllib.request import urlopen
import json
import copy

# Creating the results folder for any resulting figures to be saved
cwd = os.getcwd()
os.makedirs(os.path.dirname(cwd+'/Results/'), exist_ok=True)

def clean_epc_data(epc_data):
    """
    This function makes a few tweaks to clean up the epc_data downloaded from
    the database to make it more ready for exploratory data analysis

    INPUTS:
        - epc_data: This is in the format of a pandas dataframe. The dataframe
                likely comes from pd.read_csv for the downloaded .csv data
                from the Energy Performance of Buildings Data database here:
                https://epc.opendatacommunities.org/. (Note, this function could
                be adjusted to read in and parse that data as well, but for
                the purposes I'm just keeping the input as a dataframe)
    OUTPUTS:
        - cleaned_epc_data: This is also in the format of a pandas dataframe.
                It will be the same size and shape as epc_data.
    """
    cleaned_epc_data = copy.deepcopy(epc_data)
    cleaned_epc_data.columns = cleaned_epc_data.columns.str.replace('-', '_')
    cleaned_epc_data['full_address'] = cleaned_epc_data['address']+', '+cleaned_epc_data['postcode']

    return cleaned_epc_data

def view_portfolio_map(cleaned_epc_data, energy_efficiency_col, *positional_parameters, **keyword_parameters):
    """
    This function uses plotly express to visualise the landlord's portfolio
    and their corresponding energy ratings on an interactive map, so the landlord
    can quickly see where the areas of improvement are.

    INPUTS:
        - cleaned_epc_data: The epc_data dataframe that has been cleaned using
                the clean_epc_data function
        - energy_rating_col: The column in the cleaned_epc_data dataframe that
                describes the energy rating you want to visualise. It will be
                either 'current_energy_rating' or 'potential_energy_rating'
                depending on what you want to visualise

    OUTPUT:
        - fig: The map figure showing the landlord's portfolio
    """
    # Local authorities in the UK JSON found on Stack Overflow at
    # https://stackoverflow.com/questions/72972299/how-to-plot-a-plotly-choropleth-map-with-english-local-authorities-using-geojson

    with urlopen('https://raw.githubusercontent.com/thomasvalentine/Choropleth/main/Local_Authority_Districts_(December_2021)_GB_BFC.json') as response:
        local_authorities = json.load(response)

    # I want to add in a test here for the energy efficiency col!

    fig = px.choropleth_mapbox(
                               cleaned_epc_data,
                               geojson=local_authorities,
                               locations='local_authority_label',
                               color=energy_efficiency_col,
                               featureidkey="properties.LAD21NM",
                               color_continuous_scale="RdYlGn",
                               mapbox_style="carto-positron",
                               # Using the latitude and longitude values of wiltshire,
                               # I got it by a bit of trial and error - but would have liked to
                               # automate it if I had extra time!
                               center={"lat": 51.34, "lon": -2},
                               zoom=6.2,
                               opacity=0.7,
                               range_color=(0, 100)
                            )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    if ('save' in keyword_parameters.keys()):
        if keyword_parameters['save'] is True:
            fig.write_image('Results/{} Portfolio Map.png'.format(energy_efficiency_col))

    return fig

def get_potential_energy_efficiency_difference(cleaned_epc_data):
    """
    This function calculates the energy efficiency difference between the current
    and potential energy efficiency.

    INPUTS:
        - cleaned_epc_data: The cleaned epc_data dataframe

    OUTPUTS:
        - cleaned_epc_data: The cleaned epc_data dataframe, with an additional
            column for the potential energy efficiency difference
    """
    cleaned_epc_data['potential_energy_efficiency_difference'] = abs(cleaned_epc_data['potential_energy_efficiency']-cleaned_epc_data['current_energy_efficiency'])

    return cleaned_epc_data

def get_potential_cost_saved(cleaned_epc_data):
    """
    This function calculates the potential cost saved by combinining information
    from various current costs and potential costs in the dataframe. It returns
    the same dataframe with the extra column of 'potential_cost_saved'

    INPUTS:
        - cleaned_epc_data: The epc_data dataframe that has been cleaned using
                the clean_epc_data function

    OUTPUTS:
        - cleaned_epc_data: The epc_data dataframe that has been cleaned using
                the clean_epc_data function with the addition of the column of
                'potential_cost_saved'
    """
    cleaned_epc_data['potential_cost_saved'] = sum(
        [(cleaned_epc_data['hot_water_cost_current']-cleaned_epc_data['hot_water_cost_potential']),
        (cleaned_epc_data['heating_cost_current']-cleaned_epc_data['heating_cost_potential']),
        (cleaned_epc_data['lighting_cost_current']-cleaned_epc_data['lighting_cost_potential'])]
    )

    return cleaned_epc_data

def get_co2_emissions_potential_difference(cleaned_epc_data):
    """
    This function calculates the difference between current co2 emissions and
    potential co2 emissions

    INPUTS:
        - cleaned_epc_data: The epc_data dataframe that has been cleaned using
                the clean_epc_data function

    OUTPUTS:
        - cleaned_epc_data: The epc_data dataframe that has been cleaned using
                the clean_epc_data function with the addition of the column of
                'co2_emissions_potential_difference'
    """
    co2_diff = cleaned_epc_data['co2_emissions_current']-cleaned_epc_data['co2_emissions_potential']
    cleaned_epc_data['co2_emissions_potential_difference'] = co2_diff

    return cleaned_epc_data

def get_features(cleaned_epc_data):
    """
    A wrapper function to contain the feature engineering functions

    INPUTS:
        - cleaned_epc_data: The cleaned epc_data dataframe

    OUTPUTS:
        - cleaned_epc_data: The cleaned epc_data dataframe with the addition of
                columns: 'potential_cost_saved', 'co2_emissions_potential_difference',
                'potential_energy_efficiency_difference'
    """
    cleaned_epc_data = get_potential_energy_efficiency_difference(cleaned_epc_data)
    cleaned_epc_data = get_potential_cost_saved(cleaned_epc_data)
    cleaned_epc_data = get_co2_emissions_potential_difference(cleaned_epc_data)

    return cleaned_epc_data

def plot_scatter(cleaned_epc_data, x, y, hue, *positional_parameters, **keyword_parameters):
    """
    This function produces a scatter plot that can visualise the relationship
    between two variables, and also coloured by a third variable

    INPUTS:
        - cleaned_epc_data: The cleaned epc_data dataframe
        - x: The column from cleaned_epc_data dataframe that will be the x axis
                variable
        - y: The column from the cleaned_epc_dataframe that will be the y axis
                variable
        - hue: The column from the cleaned_epc_dataframe that will colour the
                points on the scatter plot
        (- save: Boolean, if True will save an output png in Results folder.
                default False)
        (- hue_order: The order of the legend labels)
        (- colors: A list of hex code colours for the hue)
    """
    fig = plt.figure(figsize=(5, 5))

    # Determining the colors of the points
    if ('colors' in keyword_parameters.keys()):
        colors = keyword_parameters['colors']
        if len(colors) > 1:
            customPalette = sns.set_palette(sns.color_palette(colors))
        else:
            customPalette = colors
    elif ('palette' in keyword_parameters.keys()):
        customPalette = keyword_parameters['palette']
    else:
        customPalette = 'magma'

    if ('hue_order' in keyword_parameters.keys()):
        hue_order = keyword_parameters['hue_order']
    else:
        hue_order = np.unique(hue)

    sns.scatterplot(
        data=cleaned_epc_data,
        x=x,
        y=y,
        s=200,
        hue=hue,
        hue_order=hue_order,
        palette=customPalette
    )

    if ('save' in keyword_parameters.keys()):
        if keyword_parameters['save'] is True:
            fig.savefig('Results/{} vs {} Scatter Plot.png'.format(x, y))

def property_focus_feature_analysis(
        cleaned_epc_data,
        feature_col,
        *positional_parameters,
        **keyword_parameters
        ):
    """
    This function performs an analysis based on a specific feature in the
    cleaned_epc_data dataframe. It focus on the cumulative effect of that feature,
    as the feature may not be evenly distributed between all properties. I.e.
    'potential_cost_saved' is skewed to a small selection of the properties.
    This cumulative plot shows this, and a cut off (i.e. 50%) of the total feature
    is used for analysis, and to help guide the landlord which properties to focus
    on when the feature is skewed between properties.

    INPUTS:
        - cleaned_epc_data: The cleaned epc_data dataframe
        - feature_col: The column in cleaned_epc_data which you want to perform
                the analysis on
        (- percent_line: The cut off you wish you apply to get the selected top
                    /skewed properties for the feature. Default 0.5)
        (- save: Boolean, if True will save an output png in Results folder.
                default False)
        (- address_col: The column in cleaned_epc_data that will be used as the
                x axis to represent the individual properties. Default is 'address_col')
    OUTPUTS:
        - focus_properties_df: A shrunk down version of cleaned_epc_data that
                only contains the properties which are skewed highly to the feature
                and therefore should be the focus for the landlord

    """
    # Determine what value should be along the x axis to represet the
    # property
    if ('address_col' in keyword_parameters.keys()):
        address_col = keyword_parameters['address_col']
    else:
        address_col = 'address'

    # Ordering the data from largest to smallest
    feature_data = cleaned_epc_data[[address_col, feature_col]].sort_values(by=feature_col, ascending=False)

    if ('figsize' in keyword_parameters.keys()):
        figsize = keyword_parameters['figsize']
    else:
        figsize = (12, 4)
    fig = plt.figure(figsize=figsize)

    ax = sns.barplot(
        x = feature_data[address_col],
        y = np.cumsum(feature_data[feature_col]),
        color = 'black'
        )

    # Adding in a line to show % of feature (y axis) to see how it corresponds
    # to x axis to see how skewed the distribution of the feature is between
    # properties
    if ('percent_line' in keyword_parameters.keys()):
        percent_line = keyword_parameters['percent_line']
    else:
        percent_line = 0.5
    plt.axhline(y=max(np.cumsum(feature_data[feature_col]))*percent_line, color='r', linestyle='--')

    plt.yticks(rotation='horizontal')
    plt.xticks(rotation=90)

    plt.xlabel('Property')
    plt.ylabel('Cumulative {}'.format(feature_col))

    fig = ax.get_figure()
    if ('save' in keyword_parameters.keys()):
        if keyword_parameters['save'] is True:
            fig.savefig('Results/Cumulative Feature Plot', bbox_inches='tight')

    # Calculating the percentage of properties that correspond to the percentage
    # of the feature. I.e. % of x given % of y. This helps to see how skewed the
    # data is. If the feature is evenly distributed between properties,
    # %x should be the same as %y
    percent_of_total = (sum(np.cumsum(feature_data[feature_col])<max(np.cumsum(feature_data[feature_col]))*percent_line)
     /len(np.cumsum(feature_data[feature_col])<max(np.cumsum(feature_data[feature_col]))*percent_line))*100

    conclusion_string = '{}% of the total {} across the whole portfolio is explained by only top {}% of the properties'.format(percent_line*100, feature_col, percent_of_total)
    if ('save' in keyword_parameters.keys()):
        if keyword_parameters['save'] is True:
            with open("Results/Suggestion.txt", "w") as f:
                print(conclusion_string, file=f)
                print('', file=f)
    else:
        print(conclusion_string)

    # Taking the subset of cleaned_epc_data based on the percentage of the feature
    # to investigate
    focus_properties_df = cleaned_epc_data.loc[np.cumsum(feature_data[feature_col])<max(np.cumsum(feature_data[feature_col]))*percent_line]

    return focus_properties_df

def get_recommendations(focus_properties_df):
    """
    This function produces simple recommendations based on the focus_properties_df
    which is the output of property_focus_feature_analysis. I guess this is where
    the Sero pathways engine might come in?

    INPUTS:
        - focus_properties_df: Output from property_focus_feature_analysis. The
                shrunk down version of the cleaned_epc_data dataframe that only
                contains the skewed/properties of interest based on a predetermined feature

    OUTPUTS:
        - f: The recommondations .txt file where all of the recommendations have been printed
    """
    # Identifying properties with single glazing
    glazing_rec = focus_properties_df.loc[focus_properties_df.windows_description=='Single glazed']['address'].values
    with open("Results/Recommendations.txt", "w") as f:
        print('Only single glazing in:', file=f)
        print('{}'.format(glazing_rec), file=f)
        print('Consider double or triple glazing for greater efficiency', file=f)
        print(' ', file=f)

    # Identifying properties in the subset list that dont have wall insulation
    walls_rec = focus_properties_df.loc[focus_properties_df.walls_description.str.contains('no insulation')]['address'].values
    with open("Results/Recommendations.txt", "a") as f:
        print('Walls not insulated in:', file=f)
        print('{}'.format(walls_rec), file=f)
        print('Consider insulating walls for greater efficiency', file=f)
        print(' ', file=f)

    # Identifying properties that dont have heatpumps
    heatpump_rec = focus_properties_df.loc[~focus_properties_df.mainheat_description.str.contains('heat pump')]['address'].values
    with open("Results/Recommendations.txt", "a") as f:
        print('No heat pumps in:', file=f)
        print('{}'.format(heatpump_rec), file=f)
        print('Consider installing heat pumps for greater efficiency', file=f)
        print(' ', file=f)

    # Identifying properties that have all or some low energy lighting
    lighting_rec = focus_properties_df.loc[~focus_properties_df.lighting_description.isin(['Low energy lighting in all fixed outlets'])]['address'].values
    with open("Results/Recommendations.txt", "a") as f:
        print('Some low energy lighting in:', file=f)
        print('{}'.format(lighting_rec), file=f)
        print('Consider low energy light sources throughout', file=f)
        print(' ', file=f)

    # Identifying properties that dont have floor insulation
    floor_rec = focus_properties_df.loc[focus_properties_df.floor_description.str.contains('no insulation')]['address'].values
    with open("Results/Recommendations.txt", "a") as f:
        print('No floor insulation in:', file=f)
        print('{}'.format(floor_rec), file=f)
        print('Consider installing floor insulation for greater efficiency', file=f)
        print(' ', file=f)

    f = open("Results/Recommendations.txt", "r")

    return f



def make_cost_savings_report(epc_data, *positional_parameters, **keyword_parameters):
    """
    This is a wrapper function that will run through the processing steps that
    can be accessed individually in this package, but does it all in one and
    creates a .pdf report that can be output the main outcomes of the exploratory
    analysis automatically. In theory, this function could be used for any
    epc_data for any landlord's portfolio to give them some automated insights.
    This report focus on the cost savings, and the most efficient way to make these
    cost savings for the landlord by telling them which to focus on.

    INPUTS:
        - epc_data: This is in the format of a pandas dataframe. The dataframe
                likely comes from pd.read_csv for the downloaded .csv data
                from the Energy Performance of Buildings Data database here:
                https://epc.opendatacommunities.org/. (Note, this function could
                be adjusted to read in and parse that data as well, but for
                the purposes I'm just keeping the input as a dataframe)

    """

    # EPC Rating colors
    colors = [
        '#0A8647',
        '#2EA949',
        '#95CA53',
        '#F1EC37',
        '#F6AE35',
        '#EF6F2E',
        '#E92730'
    ]
    hue_order = [
        'A',
        'B',
        'C',
        'D',
        'E',
        'F',
        'G'
    ]

    # Run through analysis, and output and save plots
    cleaned_epc_data = clean_epc_data(epc_data);
    view_portfolio_map(
        cleaned_epc_data,
        'current_energy_efficiency',
        save=True
        )
    view_portfolio_map(
        cleaned_epc_data,
        'potential_energy_efficiency',
        save=True
        )
    cleaned_epc_data = get_features(cleaned_epc_data)
    plot_scatter(
        cleaned_epc_data,
        x='potential_energy_efficiency_difference',
        y='potential_cost_saved',
        hue='current_energy_rating',
        colors=colors,
        hue_order=hue_order,
        save=True
        )
    focus_properties_df = property_focus_feature_analysis(
            cleaned_epc_data,
            'potential_cost_saved',
            save=True
            )
    recommendations = get_recommendations(focus_properties_df)

    # Create the .pdf report
    from fpdf import FPDF
    class PDF(FPDF):
        def header(self):
            self.image('https://sero.life/wp-content/uploads/2021/07/sero-group-og.png', w=50)
        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', '', 8)
            self.cell(0, 10, str(self.page_no()), 0, 0, 'C')
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(40, 10, 'Energy Efficiency & Recommendations Report')
    pdf.set_font('Arial','', 10)
    pdf.ln(10)
    pdf.cell(15,10, '')
    pdf.cell(40,10, 'Your Current Portfolio Energy Efficiency')
    pdf.cell(48,10, '')
    pdf.cell(40,10, 'Your Potential Portfolio Energy Efficiency')
    pdf.ln(10)
    ypos = pdf.get_y()
    pdf.image('Results/current_energy_efficiency Portfolio Map.png', w=90, x=23)
    pdf.set_y(ypos)
    pdf.image('Results/potential_energy_efficiency Portfolio Map.png', w=90, x=115)
    pdf.ln(5)
    pdf.set_font('Arial','', 10)
    pdf.cell(0, 4, 'Improving energy efficiency is directly related to cost savings, as shown on the scatter plot.')
    pdf.ln(5)
    pdf.cell(0, 4, 'Potential cost savings are seen to be higher in some properties than others.')
    pdf.ln(5)
    pdf.cell(0, 4, 'To make these changes most efficiently, it is helpful to view a cumulative plot to determine where to start:')
    pdf.ln(10)
    ypos = pdf.get_y()
    pdf.image('Results/potential_energy_efficiency_difference vs potential_cost_saved Scatter Plot.png', w=60)
    pdf.set_y(ypos)
    pdf.image('Results/Cumulative Feature Plot.png', w=130, x=70)
    pdf.ln(5)
    f = open("Results/Suggestion.txt", "r")
    pdf.cell(0, 4, txt=f.read())
    pdf.add_page()
    pdf.set_font('Arial','B', 14)
    pdf.cell(0, 4, 'Recommendations based on selected properties:')
    pdf.set_font('Arial','', 10)
    pdf.set_x(30)
    pdf.ln(10)
    f = open("Results/Recommendations.txt", "r")
    for x in f:
        pdf.cell(10,0,'')
        pdf.cell(0, 6, txt = x, ln = 1)
    pdf.output('Energy Efficiency and Cost Savings Report.pdf', 'F')
