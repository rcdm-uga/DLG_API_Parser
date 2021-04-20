"""
GUI that gets the required script arguments (path to input CSV, place to save output CSV, name for output CSV)
and then runs the script to create the CSV so users don't need to interact with the command line.

Probably will actually include it in the dlg_json2csv.py document itself, but experimenting with it separately.
"""
# TODO: need fields for optional encode and mapping

import csv
import os
import pandas as pd
import PySimpleGUI as sg
import re
import requests
import subprocess
import sys


def dlg_json2list(url_list):
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


"""Makes and displays a window for users to provide the input and output csv."""

sg.theme("DarkTeal6")

layout_one = [[sg.Text('Path to CSV with DLG URLs', font=("roboto", 12))],
              [sg.Text('Folder to save output', font=("roboto", 12))],
              [sg.Text('Name for the output CSV', font=("roboto", 12))],
              [sg.Text(font=("roboto", 1))],
              [sg.Submit(key="submit"), sg.Cancel()]]

layout_two = [[sg.Input(key="input_csv"), sg.FileBrowse()],
              [sg.Input(key="output_location"), sg.FolderBrowse()],
              [sg.Input(key="output_name")]]

layout_three = [[sg.Text("Mapping", font=("roboto", 12)),
                 sg.Input(key="map"), sg.FileBrowse()]]

layout = [[sg.Column(layout_one), sg.Column(layout_two)],
          [sg.Frame("Optional", layout_three, font=("roboto", 15))]]

window = sg.Window("DLG API Parser: Make a CSV from DLG Metadata", layout)

while True:
    event, values = window.read()
    if event == "submit":
        output_csv = os.path.join(values["output_location"], values["output_name"])
        # Error testing
        if values["input_csv"] == "":
            sg.Popup("CSV can't be blank")
        elif values["output_name"] == "":
            sg.Popup("Output name can't be blank")
        # Run script
        else:
            if os.path.exists(output_csv):
                override = sg.PopupYesNo("Do you want to replace existing csv?")
                # GUI remains open for data input if override is no.
                # Could do something fancy to change color of boxes with errors OR clear values if errors by updating layout.
                # TODO: work with mapping default.
                if override == "Yes":
                    make_csv(values["input_csv"], output_csv, "DLG_Mapping.csv")
            else:
                make_csv(values["input_csv"], output_csv, "DLG_Mapping.csv")
    # User closes the GUI
    if event in ("Cancel", None):
        exit()

# Not sure if we need this. Right now user closes GUI.
# Put in code where want it to auto-close, if we do, or PSG recommends.
# window.close()


# # Gets the script argument values from the user, validates the values, and reformats the information.
# # Continues giving the user the GUI and processing the input until all values are valid.
# # TODO: check all the values before giving the GUI again?
# # TODO: merge this error checking better with argparse in dlg_json2csv.py or replace it.
# message = ""
# while True:
#
#     # Displays a GUI to the user and gets input.
#     status, arguments = display_gui(message)
#
#     # If the user clicked cancel or the X on the GUI, ends the script.
#     if status in ("Cancel", None):
#         exit()
#
#     # If the provided value for the URLs CSV is empty or is not a valid path, displays the GUI again.
#     input_csv = arguments["input_csv"]
#     if input_csv == "":
#         message = "Please try again. The path to the CSV with the DLG URLs cannot be blank."
#         continue
#     elif not os.path.exists(input_csv):
#         message = "Please try again. The path to the CSV with the DLG URLs was not a valid path."
#         continue
#
#     # If the provided value for the output folder is empty or is not a valid path, displays the GUI again.
#     output_location = arguments["output_location"]
#     if output_location == "":
#         message = "Please try again. The folder to save the output to cannot be blank."
#         continue
#     elif not os.path.exists(output_location):
#         message = "Please try again. The folder to save the output to was not a valid path."
#         continue
#
#     # If the provided value for the output CSV name is empty, displays the GUI again.
#     output_file = arguments["output_name"]
#     if output_file == "":
#         message = "Please try again. The name for the output CSV cannot be blank."
#         continue
#
#     # Adds file extension to the end of the provided file name if it is not already present.
#     if not output_file.endswith(".csv"):
#         output_file = output_file + ".csv"
#
#     # Creates the path for the script output CSV using the provided values for the output location and file name.
#     output_csv = os.path.join(output_location, output_file)
#
#     # If the provided value for the mapping file (which is option) is not a valid path, displays the GUI again.
#     if not arguments["map"] == "" and not os.path.exists(arguments["map"]):
#         message = "Please try again. The path to the mapping CSV was not a valid path."
#         continue
#
#     # If all values are valid, quits the loop.
#     break

# # Runs the dlg_json2csv.py script with the user-provided information as the arguments.
# # Builds the script command by starting with the required values and then adding the optional value if provided.
# script_command = f'python dlg_json2csv.py --input "{input_csv}" --output "{output_csv}"'
# if not arguments["map"] == "":
#     script_command += f' --mapping {arguments["map"]}'
# subprocess.run(script_command, shell=True)
