This program was created to be an intermediate step to pull item(s) from the [Digital Library of Georgia's](https://dlg.usg.edu) (DLG) API and compile it into a CSV file. This script is specifically used to import the CSV with the CSVImport plugin. Please take a look at the word document `DLG_Omeka_API_Pipeline.pdf` because it explains the entire pipeline. That should give you a good feel for the task this script completes. This allows you to have the data for each item but not have to store each item on your own. You will be pulling these from DLG. 


### A Brief Description
The DLG's API returns a json file of the item(s) you're looking for with all of the
associated metadata and if copyright persist a link to the direct file. *Depending
on the copyright and the host of the item, the API may return a blank field instead
of a direct link. In this case, this program will generate the thumbnail that way
Omeka's plugin will not skip it when trying to read it in.*

The specifics about Omeka's CSVImport will be in `DLG_Omeka_API_Pipeline.pdf` file.

### Other Files
  * DLG_Mapping.\* If you want to make any changes to the column headers in your output csv, either update this csv or create your own and use the `--mapping` argument. 
  * sample_urls.txt is just a sample file that will succesfully run thorugh the program. Each of the three URLs are of different cases, illustrating that it can handle any type of URL from the DLG website. (Besides https://dlg.usg.edu obviously.)

### Dependencies
python 3+:
  1. pandas v 0.25.1+
  2. requests 2.22.0+

The reset come preinstalled with python.


### How to Run
This program is ran from the command line, thus you will need to move the command
prompt to this folder and run the following command:

`python dlg_json2list.py --input <txt file> --output <name of output csv>`

Lastly, the command line arguments:
  * `--input`: REQUIRED. The txt file that contains the url(s) to be parsed. Please make sure that you do not put any line breaks (or new lines) inside the url. There needs to be one url per line.
  * `--output`: REQUIRED. The name of the output csv you want these URL's to be added.
  * `--encode`: [Default: utf-8] If you want to change the encoding of the csv.
  * `--mapping`: [Default: DLG_Mapping.csv] The csv that contains the column mapping to change the column names of the csv instead of naming them what DLG names them.

To get a description, just run `python dlg_json2csv.py --help` for a similar description.
