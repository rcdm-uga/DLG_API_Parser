import argparse
import sys
import json
import requests
import csv
import re
import pandas as pd



def dlg_json2list(url_list):

    list_json = []

    for url in url_list:

        #Check for .json already in URL before we assume it is not there.
        is_api_url = type(re.search('.json',url)) == re.Match

        #Checking to see if url is a search result or a single item.
        is_search_result = type(re.search('\?',url)) == re.Match
        url_old = url

        if not is_api_url:
            #If this is reached, then '.json' is not present and
            #we need to add it to the url to grab API response.
            if is_search_result:
                api_url = re.sub('\?','.json?',url)

            else:
                api_url = re.sub('$','.json',url)
        else:
            #If this is reached, then the URL is already the API response.
            api_url = url



        #Grabbing the response json
        try:
            #The error check was important because of the older version,
            #but I will keep it just incase. Now that I implenmented reading
            #reading the urls from the file istead of the command line,
            #majority of the potential errors have been alleviated.

            response = requests.get(api_url)
            json_dict = response.json()

        except:
            print('Something went wrong with the url')
            print('{} is the url you are trying to parse.'.format(url_old))
            continue

        json_dict = response.json()

        if not is_search_result:
            list_json.append(json_dict['response']['document'])
        else:
            #If the URL is a search query, then we need to grab every item on
            #every page. This entire else statement handles that.

            total_pages = json_dict['response']['pages']['total_pages']
            print("Total pages:", total_pages)

            # Saves the results from the first page of the API call to the list.
            for item in json_dict['response']['docs']:
                list_json.append(item)

            # If there are multiple pages, calculates the api_url for all the other pages and adds them to the list.
            # Stops when the total number of pages is reached.
            if total_pages > 1:

                # Range produces a sequence of numbers from 2 - last page number.
                for page in range(2, total_pages + 1):
                    print("Starting page:", page)
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
                        print('Something happened on page {} of this URL: {}'.format(page, re.sub('\.json','',api_url)))

                    # Saves the response to the list.
                    for item in json_dict['response']['docs']:
                        list_json.append(item)


    #Error Check. list_json should have 1 or more items inside. otherwise exit.
    if len(list_json) < 1:
        print('Was not able to grab any of the URLs. Please check them.')
        sys.exit()
    print('done with initial api calls')

    '''
    This loop with iterate through each item of list_json to convert each
    item into a string so when creating the CSV, the excess qoutation marks and
    brackets will go away. Plus we will handle the redirecting url's and copyright
    issues with replacing the item with the thumbnails.
    '''
    for item in list_json:
        for key in item.keys():

            #Changing the list into one big string
            if type(item[key]) == list:
                text = item[key][0]
                for i in range(1,len(item[key])):
                    text += ', ' + item[key][i]
                item[key] = text

            #Changing the item URL
            if key == 'edm_is_shown_by':
                #Thumbnails
                if item[key] == None:
                    thumbnail_url = 'https://dlg.galileo.usg.edu/'
                    try:
                        repoID, collectionID, itemID = item['id'].split('_',2)
                    except:
                        print(item['id'])
                    thumbnail_url += repoID +'/'+ collectionID +'/do-th:'+ itemID

                    #Now grabbing the redirected url
                    item[key] = requests.get(thumbnail_url).url
                else:
                    #Grabbing the redirected item for the
                    try:
                        item[key] = requests.get(item[key]).url
                    except:
                        print(item[key])
    print("done with thumbnail replacement")
    return list_json

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


    url_file = args.input    #The File of URLs from the DLG
    csv_name = args.output  #The name of the CSV output file.
    encoding = args.encode  #File encoding
    dlg_mapping = args.dlg  #What to map the DLG's field names to

    #grabbing all of the URLs in the file to then be parsed
    url_list = []
    with open(url_file,'r') as dlg_urls:
        for line in dlg_urls:
            url_list.append(line.strip())

    print("starting api calls)")
    #Grabbing the complete list of jsons from the provided URLs
    list_json = dlg_json2list(url_list)
    print("reformating in the dataframe")
    df = pd.DataFrame.from_dict(list_json)

    #Initalizing the DLG Mapping dict
    new_column_name = {}

    #Grabbing the DLG Dublin Core Mapping
    with open(dlg_mapping,'r') as map_csv:
        w = csv.reader(map_csv)
        for row in w:
            new_column_name.update({row[0]:row[1]})


    #Creating Columns to drop
    drop_columns = [col for col in list(df.columns) if col not in list(new_column_name.keys())]
    df.drop(drop_columns, axis=1, inplace=True)
    print("saving to csv")
    #renaming the columns to map to Dublin Core and writing to csv
    df.rename(columns = new_column_name,inplace=True)
    df = df.sort_index(axis=1)
    df.to_csv(csv_name,index=False)
