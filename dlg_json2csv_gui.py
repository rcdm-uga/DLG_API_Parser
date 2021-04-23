"""
Parses JSON data from the DLG API into a CSV.
A GUI is used to run the script so users don't need to interact with the command line.
"""

import csv
import os
import pandas as pd
import PySimpleGUI as sg
import re
import requests
import sys


def dlg_json2list(url_list, output_location):
    """Gets the JSON from th DLG API for every value in the url_list and results it as a list.
    Makes a log for details about any problems in the same folder as the output."""
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
            with open(f'{output_location}/error_log.txt', 'a') as log:
                log.write('\n\nCould not get data from the DLG API for the following URL:')
                log.write(url)
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
                        with open(f'{output_location}/error_log.txt', 'a') as log:
                            log.write('\n\nCould not get data from the DLG API for the following page:')
                            log.write(f'Page: {page}, API URL: {api_url}')
                        continue

                    # Saves the response to the list.
                    for item in json_dict['response']['docs']:
                        json_list.append(item)

    # Error Check. json_list should have 1 or more items inside. Otherwise exit.
    if len(json_list) < 1:
        with open(f'{output_location}/error_log.txt', 'a', ) as log:
            log.write('\n\nCould not get any data from the DLG API for this request')
        sg.Popup("Unable to get any data for the provided input. See error_log.txt in the output folder for more "
                 "information.")
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
                        with open(f'{output_location}/error_log.txt', 'a') as log:
                            log.write(f'\n\nCould not parse the item id for the thumbnail url: {item["id"]}')
                        continue
                    # Now grabbing the redirected URL.
                    item[key] = requests.get(thumbnail_url).url
                else:
                    # Grabbing the redirected item.
                    try:
                        item[key] = requests.get(item[key]).url
                    except:
                        with open(f'{output_location}/error_log.txt', 'a') as log:
                            log.write(f'\n\nCould not get redirected item: {item[key]}')

    return json_list


def make_csv(url_file, csv_name, dlg_mapping, output_location):
    """Creates a CSV of data from the DLG API for all specified items. """

    # Grabbing all of the URLs in the file to then be parsed.
    urls = []
    with open(url_file, 'r') as dlg_urls:
        for line in dlg_urls:
            urls.append(line.strip())

    # Grabbing the complete list of JSONs from the provided URLs and making a dataframe.
    jsons = dlg_json2list(urls, output_location)
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

    # Communicate script success to user.
    sg.Popup("CSV has been created.")


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
    # TODO: change formatting on boxes with errors?
    if event == "submit":

        # Error testing on all of the user inputs. Required fields cannot be empty and paths must be valid.
        # Errors are saved to a list so all values can be tested prior to notifying the user.
        errors = []
        if values["input_csv"] == "":
            errors.append("Input CSV can't be blank.")
        if not os.path.exists(values["input_csv"]):
            errors.append("Input CSV path is not correct.")
        if values["output_folder"] == "":
            errors.append("Output folder cannot be blank.")
        if not os.path.exists(values["output_folder"]):
            errors.append("Output folder path is not correct.")
        if values["output_name"] == "":
            errors.append("Output name can't be blank.")
        if values["mapping_csv"] == "":
            errors.append("Mapping CSV can't be blank. Use DLG_Mapping.csv for the default.")
        if not os.path.exists(values["mapping_csv"]):
            errors.append("Mapping CSV path is not correct.")

        # If the user inputs are correct, verifies if the output CSV exists and runs the script if it does not
        # OR if the user agrees to overwrite the existing CSV. If the user does not want to overwrite an existing CSV,
        # no CSV is made and the user must resubmit the input.
        if len(errors) == 0:

            # Makes a variable for the full path to the CSV for the output from two user inputs,
            # including adding a ".csv" file extension if output_name does not already have one.
            if not values["output_name"].endswith(".csv"):
                values["output_name"] = values["output_name"] + ".csv"
            output_csv = os.path.join(values["output_folder"], values["output_name"])

            # If the CSV for the script output already exists, prompt the user to decide if it should be overwritten.
            # If the user indicates yes, the script is run. Otherwise, the user can correct the input and resubmit.
            if os.path.exists(output_csv):
                override = sg.PopupYesNo("Do you want to replace the existing CSV?")
                if override == "Yes":
                    make_csv(values["input_csv"], output_csv, values["mapping_csv"], values["output_folder"])
            else:
                make_csv(values["input_csv"], output_csv, values["mapping_csv"], values["output_folder"])

        # If some of the user inputs were not correct, creates a pop up box with the errors.
        # The user may then edit the provided input and resubmit.
        else:
            error_message = "\n".join(errors)
            sg.Popup(error_message)

    # If the user clicked cancel or the X on the GUI, quites the script.
    if event in ("Cancel", None):
        exit()
