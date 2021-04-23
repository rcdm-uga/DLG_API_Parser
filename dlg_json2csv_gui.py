"""
Parses JSON data from the DLG API into a CSV.
A GUI is used to run the scriptso users don't need to interact with the command line.
"""

import csv
import os
import pandas as pd
import PySimpleGUI as sg
import re
import requests
import sys


def dlg_json2list(url_list):
    """Gets the JSON from th DLG API for every value in the url_list and results it as a list."""
    json_list = []

    for url in url_list:

        # Creates an API URL from the provided URL. Adds .json if not present, which goes in a different location
        # depending on if the provided URL is from a search or for a single item.
        is_api_url = type(re.search('.json', url)) == re.Match
        is_search_result = type(re.search(r'\?', url)) == re.Match
        if not is_api_url:
            if is_search_result:
                api_url = re.sub(r'\?', '.json?', url)
            else:
                api_url = re.sub(r'$', '.json', url)
        else:
            api_url = url

        # Grabbing the response JSON.
        try:
            # The error check was important because of the older version, but I will keep it just in case. Now that I
            # implemented reading the urls from the file instead of the command line, majority of the potential
            # errors have been alleviated.
            response = requests.get(api_url)
            json_dict = response.json()
        except:
            print('Something went wrong with the url')
            print('{} is the url you are trying to parse.'.format(url))
            continue

        # Saving the response JSON to json_list.
        if not is_search_result:
            json_list.append(json_dict['response']['document'])

        # If the URL is a search query, then we need to grab every item on every page.
        else:
            total_pages = json_dict['response']['pages']['total_pages']

            # Saves the results from the first page of the API call to the list.
            for item in json_dict['response']['docs']:
                json_list.append(item)

            # If there are multiple pages, calculates the api_url for all the other pages and adds them to the list.
            # Stops when the total number of pages is reached.
            if total_pages > 1:

                # Range produces a sequence of numbers from 2 - last page number.
                for page in range(2, total_pages + 1):

                    # Create the api_url for the next page.
                    page_str = 'page=' + str(page)
                    if type(re.search(r'page=\d+', api_url)) == re.Match:
                        api_url = re.sub(r'page=\d+', page_str, api_url)
                    else:
                        # For the first iteration, which doesn't have 'page=\d' yet.
                        page_str = '?' + page_str + '&'
                        api_url = re.sub(r'\?', page_str, api_url)

                    # Grabbing the response and JSON for the new api_url.
                    try:
                        response = requests.get(api_url)
                        json_dict = response.json()
                    except:
                        print('Something happened on page {} of this URL: {}'.format(page, api_url))
                        continue

                    # Saves the response to the list.
                    for item in json_dict['response']['docs']:
                        json_list.append(item)

    # Error Check. json_list should have 1 or more items inside. Otherwise exit.
    if len(json_list) < 1:
        print('Was not able to grab any of the URLs. Please check them.')
        sys.exit()

    '''This loop with iterate through each item of json_list to convert each item into a string so when creating the 
    CSV, the excess quotation marks and brackets will go away. Plus we will handle the redirecting URLs and copyright 
    issues with replacing the item with the thumbnails. '''
    for item in json_list:
        for key in item.keys():

            # Changing the list into one big string.
            if type(item[key]) == list:
                text = item[key][0]
                for i in range(1, len(item[key])):
                    text += ', ' + item[key][i]
                item[key] = text

            # Changing the item URL.
            if key == 'edm_is_shown_by':
                # Thumbnails.
                if item[key] is None:
                    thumbnail_url = 'https://dlg.galileo.usg.edu/'
                    try:
                        repo_id, collection_id, item_id = item['id'].split('_', 2)
                        thumbnail_url += repo_id + '/' + collection_id + '/do-th:' + item_id
                    except:
                        print("Could not parse item_id for thumbnail_url:", item['id'])
                        continue
                    # Now grabbing the redirected URL.
                    item[key] = requests.get(thumbnail_url).url
                else:
                    # Grabbing the redirected item.
                    try:
                        item[key] = requests.get(item[key]).url
                    except:
                        print("Could not get redirected item:", item[key])

    return json_list


def make_csv(url_file, csv_name, dlg_mapping='DLG_Mapping.csv'):
    """Creates a CSV of data from the DLG API for all specified items. """

    # Grabbing all of the URLs in the file to then be parsed.
    urls = []
    with open(url_file, 'r') as dlg_urls:
        for line in dlg_urls:
            urls.append(line.strip())

    # Grabbing the complete list of JSONs from the provided URLs and making a dataframe.
    jsons = dlg_json2list(urls)
    df = pd.DataFrame.from_dict(jsons)

    # Initializing the DLG Mapping dict.
    new_column_name = {}

    # Grabbing the DLG Dublin Core Mapping.
    with open(dlg_mapping, 'r') as map_csv:
        w = csv.reader(map_csv)
        for row in w:
            new_column_name.update({row[0]: row[1]})

    # Dropping columns from the dataframe if they are not in the DLG Mapping.
    drop_columns = [col for col in list(df.columns) if col not in list(new_column_name.keys())]
    df.drop(drop_columns, axis=1, inplace=True)

    # Renaming the columns to map to Dublin Core and writing to CSV.
    df.rename(columns=new_column_name, inplace=True)
    df = df.sort_index(axis=1)
    df.to_csv(csv_name, index=False)


# Defines a GUI for users to provide the input needed for this script and
# to receive messages about errors to their inputs and the script progress.

sg.theme("DarkTeal6")

layout_one = [[sg.Text('Path to CSV with DLG URLs', font=("roboto", 12))],
              [sg.Text('Folder to save output', font=("roboto", 12))],
              [sg.Text('Name for the output CSV', font=("roboto", 12))],
              [sg.Text(font=("roboto", 1))],
              [sg.Submit(key="submit"), sg.Cancel()]]

layout_two = [[sg.Input(key="input_csv"), sg.FileBrowse()],
              [sg.Input(key="output_folder"), sg.FolderBrowse()],
              [sg.Input(key="output_name")]]

layout_three = [[sg.Text("Mapping", font=("roboto", 12)),
                 sg.Input(default_text="DLG_Mapping.csv", key="mapping_csv"), sg.FileBrowse()]]

layout = [[sg.Column(layout_one), sg.Column(layout_two)],
          [sg.Frame("Optional", layout_three, font=("roboto", 15))]]

window = sg.Window("DLG API Parser: Make a CSV from DLG Metadata", layout)

# Keeps the GUI open until the user quits the program. Receives user input, verifies the input,
# and when all input is correct runs the program.
# TODO: add a "reset" button to get the GUI back to original values if their next input is completely different.
while True:

    # Gets the user input data and saves the input values to their own variables for easier referencing in the script.
    event, values = window.read()

    # If the user submitted values, tests they are correct. If not, errors are displayed. If yes, the script is run.
    # TODO: test for all possible errors at once before displaying?
    # TODO: change formatting on boxes with errors?
    if event == "submit":

        # Makes a variable for the full path to the CSV for the output from two user inputs,
        # including adding a ".csv" file extension if output_name does not already have one.
        if not values["output_name"].endswith(".csv"):
            values["output_name"] = values["output_name"] + ".csv"
        output_csv = os.path.join(values["output_folder"], values["output_name"])

        # Error testing on all of the user inputs. Required fields cannot be empty and paths must be valid.
        # Only runs the script if all user inputs are valid.
        if values["input_csv"] == "":
            sg.Popup("Input CSV can't be blank.")
        elif not os.path.exists(values["input_csv"]):
            sg.Popup("Input CSV path is not correct.")
        elif values["output_folder"] == "":
            sg.Popup("Output folder cannot be blank.")
        elif not os.path.exists(values["output_folder"]):
            sg.Popup("Output folder path is not correct.")
        elif values["output_name"] == "":
            sg.Popup("Output name can't be blank.")
        elif values["mapping_csv"] == "":
            sg.Popup("Mapping CSV can't be blank. Use DLG_Mapping.csv for the default.")
        elif not os.path.exists(values["mapping_csv"]):
            sg.Popup("Mapping CSV path is not correct.")
        else:
            # If the CSV for the script output already exists, prompt the user to decide if it should be overwritten.
            # If the user indicates yes, the script is run. Otherwise, the user can correct the input and resubmit.
            if os.path.exists(output_csv):
                override = sg.PopupYesNo("Do you want to replace existing csv?")
                if override == "Yes":
                    make_csv(values["input_csv"], output_csv, values["mapping_csv"])
            else:
                make_csv(values["input_csv"], output_csv, values["mapping_csv"])

    # If the user clicked cancel or the X on the GUI, quites the script.
    if event in ("Cancel", None):
        exit()