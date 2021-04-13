"""
GUI that gets the required script arguments (path to input CSV, place to save output CSV, name for output CSV)
and then runs the script to create the CSV so users don't need to interact with the command line.

Probably will actually include it in the dlg_json2csv.py document itself, but experimenting with it separately.
"""
# TODO: need fields for optional encode and mapping

import os
import PySimpleGUI as sg
import subprocess


def display_gui(message_text):
    """Makes and displays a window for users to provide the input and output csv."""

    sg.theme("DarkTeal6")

    # TODO: can a field be required? Right now lets you submit them blank.
    #     https://pysimplegui.readthedocs.io/en/latest/cookbook/#recipe-input-validation
    # TODO: format message text so it is more visible
    layout = [[sg.Text(message_text, text_color="yellow")],
              [sg.Text('Path to CSV with DLG URLs'), sg.Input(key="input_csv"), sg.FileBrowse()],
              [sg.Text('Folder to save output'), sg.Input(key="output_location"), sg.FolderBrowse()],
              [sg.Text('Name for the output CSV'), sg.Input(key="output_name")],
              [sg.Submit(), sg.Cancel()]]

    window = sg.Window("Make an Omeka CSV from DLG JSON", layout)
    event, values = window.read()
    window.close()

    return event, values


# Gets the script argument values from the user, validates the values, and reformats the information.
# Continues giving the user the GUI and processing the input until all values are valid.
message = ""
while True:

    # Displays a GUI to the user and gets input.
    status, arguments = display_gui(message)

    # If the user clicked cancel or the X on the GUI, endd the script.
    if status in ("Cancel", None):
        exit()

    # If the provided value for the URLs CSV is empty or is not a valid path, displays the GUI again.
    input_csv = arguments["input_csv"]
    if input_csv == "":
        message = "Please try again. The path to the CSV with the DLG URLs cannot be blank."
        continue
    elif not os.path.exists(input_csv):
        message = "Please try again. The path to the CSV with the DLG URLs was not a valid path."
        continue

    # If the provided value for the output folder is empty or is not a valid path, displays the GUI again.
    output_location = arguments["output_location"]
    if output_location == "":
        message = "Please try again. The folder to save the output to cannot be blank."
        continue
    elif not os.path.exists(output_location):
        message = "Please try again. The folder to save the output to was not a valid path."
        continue

    # If the provided value for the output CSV name is empty, displays the GUI again.
    output_file = arguments["output_name"]
    if output_file == "":
        message = "Please try again. The name for the output CSV cannot be blank."
        continue

    # Adds file extension to the end of the provided file name if it is not already present.
    if not output_file.endswith(".csv"):
        output_file = output_file + ".csv"

    # Creates the path for the script output CSV using the provided values for the output location and file name.
    output_csv = os.path.join(output_location, output_file)

    # If all values are valid, quits the loop.
    break

# Runs the dlg_json2csv.py script with the user-provided information as the arguments.
subprocess.run(f'python dlg_json2csv.py --input "{input_csv}" --output "{output_csv}"', shell=True)
