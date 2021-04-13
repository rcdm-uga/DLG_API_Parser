# The goal is a GUI that gets the script arguments (path to input CSV, place to save output CSV, name for output CSV)
# and then runs the script. Probably would actually include it in the dlg_json2csv.py document itself, but
# experimenting with it separately.
# TODO: need fields for optional encode and mapping

import os
import PySimpleGUI as sg
import subprocess

sg.theme("DarkTeal6")

# TODO: give a default value for the output file name?
# TODO: can a field be required? Right now lets you submit them blank.
#     https://pysimplegui.readthedocs.io/en/latest/cookbook/#recipe-input-validation
layout = [[sg.Text('Path to CSV to DLG URLs'), sg.Input(key="input_csv"), sg.FileBrowse()],
          [sg.Text('Folder to save output'), sg.Input(key="output_location"), sg.FolderBrowse()],
          [sg.Text('Name for the output CSV'), sg.Input(key="output_name")],
          [sg.Submit(), sg.Cancel()]]

window = sg.Window("Make an Omeka CSV from DLG JSON", layout)
event, values = window.read()
window.close()

input_csv = values["input_csv"]

output_file = values["output_name"]
if not output_file.endswith(".csv"):
    output_file = output_file + ".csv"

# TODO: at least for printing, the slashes in the URL are going both directions.
output_csv = os.path.join(values["output_location"], output_file)

# print(input_csv)
# print(output_csv)

subprocess.run(f'python dlg_json2csv.py --input "{input_csv}" --output "{output_csv}"', shell=True)
