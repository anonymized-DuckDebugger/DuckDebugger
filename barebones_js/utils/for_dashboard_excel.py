#!/usr/bin/env python3
import utils
import yaml
import csv
import os

# this is a mere helper script.
# it converts available exercises 
# into rows to be imported into ctfd
# as part of the CSC - hence internal.

OUTFILE = '/mnt/hgfs/_sharedFolder/_rndrExercises.csv'

yaml_file_path = f'{os.path.abspath("..")}/exercises.yaml'
with open(yaml_file_path, 'r') as file:
    data = yaml.safe_load(file)

# Convert to CSV format, each key as a row and its associated data as columns
csv_data = []
for key, values in data.items():
    try:
        displayName=f"[{values.get('source','').split('.')[-1]}]"+utils.get_exercise_displayName(utils.find_exercise_folder(key))
        description = f"""Access the challenge through the following  <a target="_blank" href='https://review.redacted-domain.tld/review/{key}'>link.</a>"""
        row = [displayName, description] + [values.get(field, '') for field in ('flag', 'disabled', 'source')]
        csv_data.append(row)
    except:
        pass

# Write to CSV file
with open(OUTFILE, 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)
