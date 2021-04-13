"""
GUI that gets the required script arguments (path to input CSV, place to save output CSV, name for output CSV)
and then runs the script to create the CSV so users don't need to interact with the command line.

Probably will actually include it in the dlg_json2csv.py document itself, but experimenting with it separately.
"""
# TODO: need fields for optional encode and mapping

import os
import PySimpleGUI as sg
import subprocess


def display_gui():
    """Makes and displays a window for users to provide the input and output csv."""

    sg.theme("DarkTeal6")

    # TODO: can a field be required? Right now lets you submit them blank.
    #     https://pysimplegui.readthedocs.io/en/latest/cookbook/#recipe-input-validation
    layout = [[sg.Text('Path to CSV to DLG URLs'), sg.Input(key="input_csv"), sg.FileBrowse()],
              [sg.Text('Folder to save output'), sg.Input(key="output_location"), sg.FolderBrowse()],
              [sg.Text('Name for the output CSV'), sg.Input(key="output_name")],
              [sg.Submit(), sg.Cancel()]]

    window = sg.Window("Make an Omeka CSV from DLG JSON", layout)
    event, values = window.read()
    window.close()

    return values


# Gets the script argument values from the user
arguments = display_gui()

# Validates and reformats the information provided by the user.

# TODO: test this is a valid path and not empty.
input_csv = arguments["input_csv"]

output_file = arguments["output_name"]
if not output_file.endswith(".csv"):
    output_file = output_file + ".csv"

# TODO: test output_location is a valid path and neither are empty.
output_csv = os.path.join(arguments["output_location"], output_file)

# Runs the dlg_json2csv.py script with the user-provided information as the arguments.
subprocess.run(f'python dlg_json2csv.py --input "{input_csv}" --output "{output_csv}"', shell=True)
