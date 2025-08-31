#!/bin/bash

#### This script is basically the "undo" button for genChalYaml.py
#### It removes the last added entry in ../exercises.yaml
#### as well as the most recently created file in ../snippets_rendered

yaml_file="../exercises.yaml"
exercises_dir="../exercises"

# Check if the YAML file exists
if [ -f "$yaml_file" ]; then
    # Use awk to identify the last line that starts with [a-zA-Z0-9]
    last_line=$(awk '/^[a-zA-Z0-9]/ {last=$0} END {print last}' "$yaml_file")
    echo "Contents after '$last_line' will be removed from $yaml_file"

    # Check if the last_line is not empty (i.e., if it found a match)
    if [ -n "$last_line" ]; then
        # Do you want to cross the Rubicon?
        read -p "Are you sure you want to perform these actions? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "Script execution canceled."
            exit 0
        fi
        # Use sed to delete all lines starting from the last matching line
        sed -i "/^$last_line\$/, \$d" "$yaml_file"
        echo "Contents after '$last_line' removed from $yaml_file"
    else
        echo "No line starting with [a-zA-Z0-9] found in $yaml_file"
    fi
else
    echo "YAML file not found: $yaml_file"
fi

# Check if the exercises directory exists
if [ -d "$exercises_dir" ]; then
    most_recent_folder=$(find "$exercises_dir" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -nr | head -n 1 | cut -d' ' -f2-)
    if [ -n "$most_recent_folder" ]; then
        folder_name=$(basename "$most_recent_folder")
        read -p "Do you want to remove the most recent folder ('$folder_name')? (yes/no): " answer
        if [ "$answer" = "yes" ]; then
            rm -rf "$most_recent_folder"
            echo "Most recent folder removed: '$folder_name'"
        else
            echo "Folder removal canceled."
        fi
    else
        echo "No folders found in: $exercises_dir"
    fi
else
    echo "Directory not found: $exercises_dir"
fi