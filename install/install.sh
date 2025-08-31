#!/bin/bash

# Terminal shenanigans to make life pretty
_BOLD='\033[1m' _NORMAL='\033[0m'

# Programming languages for which SDKs/runtimes and SAST will be installed
LANGUAGES=(
    'csharp'
    'go'
    'java'
    'python'
)

# Check if we're running this script as its makers intended
if [ -z "$QUACK" ]; then
    echo "This script should be run via the Makefile."
    exit 1
fi

echo -e "$_BOLD Installing base requirements... $_NORMAL"
# ---> TODO actual install <--- #
echo -e "$_BOLD Done installing base requirements. $_NORMAL"

if [ -n "$1" ]; then
    if [ "$1" != "dev" ]; then
        # shouldn't end up here if you use the Makefile.
        echo -e "$_BOLD The argument is not 'dev'. Exiting. Use the Makefile! $_NORMAL"
        exit 1
    else
        echo -e "$_BOLD Installing dev requirements... $_NORMAL"
    fi
fi
 
# Iterate over the LANGUAGES and call the respective install script
for lang in "${LANGUAGES[@]}"; do
    script_name="install_$lang.sh"

    if [ -f "$script_name" ]; then
        echo -e "$_BOLD    Installing $lang...            [$lang]$_NORMAL"
        ./"$script_name"

        # Check if the script executed successfully
        if [ $? -ne 0 ]; then
            echo "_BOLDInstallation of $lang failed.            [$lang]$_NORMAL"
            exit 1
        fi
    else
        echo "$_BOLD[FATAL] Installation script for $lang not found: $script_name $_NORMAL"
        exit 1
    fi
done

