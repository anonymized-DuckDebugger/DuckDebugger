#!/usr/bin/env python3
import yaml
import uuid

###########################################################################
# This is an auxilliary script for developing quizzes.
# It is meant to be used for replacing quiz/question keys with random UUIDs
#     i.e. if during development of new quizzes
#          predictable placeholders were used.
#
# NOTE: currently this script overwrites quizzes.yaml.
#       use with caution
###########################################################################
def genIDstr():
    while True:
        uid_str = str(uuid.uuid4())[24:]
        try:
            int(uid_str)
        except ValueError:
            return uid_str

def update_yaml_ids(file_path, start_line=226):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Reload from line 226 onward as a string to parse
    yaml_str = ''.join(lines[start_line-1:])
    data = yaml.safe_load(yaml_str)

    # Function to replace IDs with unique UUIDs
    def replace_ids(data):
        if isinstance(data, dict):
            if 'id' in data:
                data['id'] = genIDstr()
            for key, value in data.items():
                replace_ids(value)
        elif isinstance(data, list):
            for item in data:
                replace_ids(item)

    replace_ids(data)

    # Reconstruct the YAML and write it back to file
    updated_yaml_str = yaml.dump(data, sort_keys=False)
    with open(file_path, 'w') as file:
        file.writelines(lines[:start_line-1])  # Write original lines up to 226
        file.write(updated_yaml_str)  # Write modified content


if __name__ == "__main__":
    # Run the function with your YAML file path
    update_yaml_ids('quizzes.yaml')
