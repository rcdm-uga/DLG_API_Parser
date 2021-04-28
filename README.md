# DLG API Parser

This program was created to be an intermediate step to pull item(s) from the [Digital Library of Georgia's](https://dlg.usg.edu) (DLG) API and compile it into a CSV file. This script is specifically used to import the CSV with the CSVImport plugin, although it can be adapted for other purposes by changing the mapping csv. Please take a look at the word document `DLG_Omeka_API_Pipeline.pdf` because it explains the entire pipeline. That should give you a good feel for the task this script completes. This allows you to have the data for each item but not have to store each item on your own. You will be pulling these from DLG. 


### A Brief Description
The DLG's API returns a json file of the item(s) you're looking for with all of the
associated metadata and if copyright persist a link to the direct file. *Depending
on the copyright and the host of the item, the API may return a blank field instead
of a direct link. In this case, this program will generate the thumbnail that way
Omeka's plugin will not skip it when trying to read it in.*

The specifics about Omeka's CSVImport will be in `DLG_Omeka_API_Pipeline.pdf` file.

### Other Files
   * **Command Line Instructions**: The script was originally designed to run via the command line and can still be operated that way instead of using the Windows executable for any who prefer the command line or are working in a Mac environment.


   * **DLG_Mapping.csv**: Indicates the fields from the DLG JSON that should be included in the CSV and what the columns should be named. If you want to make any changes to the column headers in your output CSV, either update this CSV or create your own.


   * **DLG_Mapping.xls**: Provides details about each field in the DLG JSON.


   * **DLG_Omeka_API_Pipeline**: A complete workflow using this script to export information from DLG about selected images and import it into Omeka for creating digital exhibits. The Word and PDF versions are the same information.


   * **sample_urls.txt** is just a sample file that will successfully run through the program. Each of the three URLs are of different cases, illustrating that it can handle any type of URL from the DLG website. (Besides https://dlg.usg.edu)

### How to Run
1. Download the executable and save it to your local machine. 
2. Save a copy of DLG_Mapping.csv or the mapping CSV you want to use in the same folder as the executable.
3. Double-click on the executable to start the program.
4. Enter the required information into the program.
   * Path to file with DLG URLs: the text file with the URLs you wish to include in the CSV
   * Folder to save output: any folder on your local machine, where the CSV and the script log are saved
   * Name for the output CSV: whatever name the output CSV should have. You may include the file extension (.csv) or have the script add it.
5. Click Submit.
