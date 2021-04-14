import argparse
import sys
import requests
import csv
import re
import pandas as pd


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
                        print("Could not parse item_id for thumbail_url:", item['id'])
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


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Makes requests to the DLG \
                        API to then parse into a CSV. Then mapped to follow the \
                        DLGs column mapping to be uploaded into Omeka via CSV Import')

    parser.add_argument('--input', dest='input', type=str, required=True,
                        help=' The file that contains the URLs. \
                        Make sure there is one URL on each line of the file.')
    parser.add_argument('--output', dest='output', type=str, required=True,
                        help='The name of the output CSV file.')
    parser.add_argument('--encode', dest='encode', type=str, default='utf-8',
                        help='The encoding preferred when writing to csv. [Default: UTF-8]')
    parser.add_argument('--mapping', dest='dlg', type=str, default='DLG_Mapping.csv',
                        help='The name of the dlg mapping CSV for column headings. \
                        Default: DLG_Mapping.csv')
    args = parser.parse_args()

    url_file = args.input  # The file of URLs from the DLG.
    csv_name = args.output  # The name of the CSV output file.
    encoding = args.encode  # File encoding.
    dlg_mapping = args.dlg  # What to map the DLG's field names to.

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
