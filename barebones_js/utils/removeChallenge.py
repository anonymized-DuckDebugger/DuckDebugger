#!/usr/bin/env python3

import argparse
import yaml
import os

currentScriptDir   = os.path.dirname(os.path.abspath(__file__))

def delete_yaml_entry(yaml_file, file_source_value):
    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # Find and delete the entry with the specified file_source value
    keys_to_delete = [key for key, value in data.items() if value.get('file_source') == file_source_value]
    for key in keys_to_delete:
        del data[key]

    with open(yaml_file, 'w') as f:
        yaml.safe_dump(data, f)

def find_files_to_delete(root_dir, file_source_value, keep_source=False):
    found_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.startswith(file_source_value):
                full_path = os.path.join(dirpath, filename)
                if keep_source and filename.endswith(file_source_value):
                    continue
                found_files.append(full_path)
    return found_files

def main():
    parser = argparse.ArgumentParser(description="Delete YAML entry and associated files.")
    parser.add_argument("file_source_value", help="The file_source value to search for in the YAML file.")
    parser.add_argument("--keepSource", action="store_true", help="Keep the exercise source code file.")

    args = parser.parse_args()

    yaml_file = f'{currentScriptDir}/../exercises.yaml'
    file_source_value = args.file_source_value

    # Delete the YAML entry
    delete_yaml_entry(yaml_file, file_source_value)

    # Find and delete the files
    found_files = find_files_to_delete('..', file_source_value, args.keepSource)
    if found_files:
        print("Found the following files:")
        for f in found_files:
            print(f)
        confirm = input("Do you want to delete these files?\nOnly a full 'yes' confirms: ")
        if confirm.lower() == 'yes':
            for f in found_files:
                os.remove(f)
            print("Files deleted.")
        else:
            print("We're done here.")
    else:
        print("No files found.")

if __name__ == "__main__":
    main()
