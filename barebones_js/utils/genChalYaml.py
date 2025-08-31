#!/usr/bin/env python3

from utils     import getExtension, getLang, find_exercise_folder
from run_sast  import run_all
import pygments_stuff
import argparse
import glob
import yaml
import uuid
import json
import sys
import os

scriptDir   = os.path.dirname(os.path.abspath(__file__))

### --- CLI --- ###
parser = argparse.ArgumentParser(description="dev util to quickly add new exercises or modify existing ones.")
parser.add_argument("codeSnippetFileName", help="Code snippet filename")
parser.add_argument("exerciseNameOrUUID", help="[new] Exercise display name / [update] exerciseUUID")
parser.add_argument("--update", action="store_true", help="Updates an existing exercise. Requires --uuid argument")
parser.add_argument("--dry", action="store_true", help="Dry run (prints to stdout, no writing to exercises.yaml)")
parser.add_argument("--type", default="review", choices=["review", "quiz"], help="Type of exercise.")
parser.add_argument("--update_uuid", help="Exercise UUID. To be used in conjunction with --update.")

# Example usage
# 1. [Generating a new challenge from a source file]
#     ./genChalYaml.py --type review someSourceCode.cs "Your awesome challenge name"
#                                      ^- must be under snippets/
# 2. [Updating an existing exercise]
#     ./genChalYaml.py someSourceCode.cs "exerciseUUID" --update


args = parser.parse_args()

codeSnippetFile           = args.codeSnippetFileName
exerciseDisplayNameOrUUID = args.exerciseNameOrUUID
exerciseType              = args.type
dry_run                   = args.dry
update                    = args.update
### ---/CLI --- ###

# Exercise metadata
if not update:
    exerciseUuid        = str(uuid.uuid4())[24:]
    exerciseDisplayName = exerciseDisplayNameOrUUID
    exerciseFolder      = os.path.abspath(f"{scriptDir}/../exercises/{exerciseDisplayName}__{exerciseUuid}")

else:    
    exerciseUuid        = exerciseDisplayNameOrUUID
    exerciseFolder      = [f for f in glob.glob(f'{scriptDir}/../exercises/*') if f.endswith(exerciseUuid)][0]
    print(f"{exerciseFolder}")
    exerciseDisplayName = exerciseFolder.split('/')[-1].split('__')[-2]

    
snippetLang      = getLang(codeSnippetFile)
exerciseFolder   = os.path.abspath(f"{scriptDir}/../exercises/{snippetLang}__{exerciseDisplayName}__{exerciseUuid}")


# Step 1. Create exercise folder and populate with:
#           - symlink to snippet (relative path)
if not update:
    try:
        os.makedirs(exerciseFolder, exist_ok=True)
        print(f"Directory '{exerciseFolder}' created successfully.")
        try:
            os.symlink(f'../../snippets/{codeSnippetFile}', f'{exerciseFolder}/{codeSnippetFile}')
        except OSError as error:
            print(f"Creation of snippet symlink failed. Error: {error}")
    except OSError as error:
        print(f"Creation of the directory '{exerciseFolder}' failed. Error: {error}")
else:
    if not os.path.exists(exerciseFolder):
        print(f"[genChalYaml][ERROR] Looks like {exerciseFolder} does not exist. Exiting...")
        sys.exit(-3)
    if not os.path.islink(f"{exerciseFolder}/{codeSnippetFile}") \
        and \
       not os.path.exists(f"{exerciseFolder}/{codeSnippetFile}"):
        print(f"[genChalYaml][ERROR] Looks like {exerciseFolder}/{codeSnippetFile} does not exist or the symlink is broken. Exiting...")
        sys.exit(-3)

# Step 2. Perform code highlighting (both new and update)
(highlightedCode, style, solutionComments) = pygments_stuff.highlightHtml(codeSnippetFile, prog_lang=snippetLang)

pygments_stuff.saveCodeAsHtml(highlightedCode, style, codeSnippetFile, dryRun=dry_run,
                              savePath=exerciseFolder, update=update) # save highlighted snippet (overwrite controlled by update flag)


# Write the (placeholder) solution to a file
with open(f'{exerciseFolder}/{codeSnippetFile}.solution', 'w') as f:        
        if not len(solutionComments): # placeholder solution.
            _placeholder_solution="1: |\n  If you're a participant and you see this, tell the trainers.\n"
            print(f"{'*'*30}\n[genChalYaml][WARNING] >>>>>>> No solution found. Defaulting to placeholder. <<<<<<<\n{'*'*30}")
            f.write(_placeholder_solution)
        else:
            for line_number, comment in solutionComments.items():
                f.write(f"{line_number}: |\n  {comment}\n")

# save style file if it doesn't exist yet
styleFile   = f"static/style.{getExtension(codeSnippetFile)}.css"
styleFilePath = f"{scriptDir}/../{styleFile}"
if not os.path.exists(styleFilePath):
    print("[pygments_stuff]: Style file didn't exist, creating our own.")
    with open(styleFilePath, 'w') as f:
        f.write(style)


# Run SAST tools and generate html snippets from the findings
run_all(filename=codeSnippetFile, savePath=exerciseFolder)

print(f"\n{'-'*80}\n{'-'*80}\n{'-'*80}\nDONE. All files can be found at:\n {exerciseFolder}")

if not update:
    newYamlEntry = {
            exerciseUuid: {
                "source": codeSnippetFile,
                "flag"  : str(uuid.uuid4())[24:],
            }
        }
    if dry_run:
        msg = "\n\nThe following would be added to the exercises.yaml file:"
        print(msg)
        print(yaml.dump(newYamlEntry))
    else:
        msg = "\n\nAdded to yaml file:"
        print(msg)
        print(yaml.dump(newYamlEntry))

        # Read the existing YAML data (if the file exists)
        yaml_path = f"{scriptDir}/../exercises.yaml"
        if os.path.exists(yaml_path):
            with open(yaml_path, 'a') as file:
                file.write('\n')
                yaml.dump(newYamlEntry, file, default_flow_style=False)

        else: # If the file doesn't exist, create it and write the new entry
            with open(yaml_path, 'w') as file:
                yaml.dump(newYamlEntry, file, default_flow_style=False)


# Uncomment to get the highlighted code html in stdout
# if dry_run:
#     print(f"{'-'*10} [ Highlighted Code ] {'-'*10}")
#     print(highlightedCode)