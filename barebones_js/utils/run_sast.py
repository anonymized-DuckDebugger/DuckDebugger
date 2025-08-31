#!/usr/bin/env python3
from   utils      import getLang, lang2sast, getJustFilename
from   jinja2     import Template
import subprocess
import argparse
import requests
import glob
import json
import sys
import os

currentScriptPath = os.path.dirname(os.path.abspath(__file__))

# ------- [ SAST EXTRAS ] ------- #
# if output isn't in SARIF format
# a conversion function is needed

def bandit_to_sarif(bandit_output):
    sarif_output = {
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "Bandit",
                    "version": "1.7.0",  # Update this to your Bandit version
                    "informationUri": "https://github.com/PyCQA/bandit",
                    "rules": []
                }
            },
            "results": []
        }]
    }

    for issue in bandit_output["results"]:
        rule_id = issue["test_id"]
        sarif_output["runs"][0]["tool"]["driver"]["rules"].append({
            "id": rule_id,
            "name": issue["test_name"],
            "fullDescription": {
                "text": issue["issue_text"]
            },
            "helpUri": issue["more_info"]
        })

        sarif_output["runs"][0]["results"].append({
            "ruleId": rule_id,
            "message": {
                "text": issue["issue_text"]
            },
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": issue["filename"]
                    },
                    "region": {
                        "startLine": issue["line_number"]
                    }
                }
            }]
        })

    return sarif_output


# ------- [ SAST TOOLS ] ------- #
# ------------------------------ #

# new tool = new functions
#   naming convention for functions:
#       run_<tool_name>(filename, language):
#   also add the function below in function_map!

# sast output convention:
#   OUTPUT PATH: dev_utils/tmp
#   FORMAT: export as sarif when available, convert when not.
#   NAME: <filename>.<tool>.tmp           ---> when output is Sarif
#   NAME: <filename>.<tool>_<format>.temp ---> when output is NOT Sarif
#                                   ^---- NOTE: temp vs tmp is important!

# -- SonarQube -- # -- SonarQube -- # -- SonarQube -- # -- SonarQube -- # -- SonarQube -- #
# -- SonarQube -- # -- SonarQube -- # -- SonarQube -- # -- SonarQube -- # -- SonarQube -- #
# -- SonarQube -- # -- SonarQube -- # -- SonarQube -- # -- SonarQube -- # -- SonarQube -- #
# Variables
SONAR_URL = "http://localhost:9000"
PROJECT_KEY = "test_1"
API_TOKEN = os.environ.get('SONARQUBE_TOKEN')
API_ENDPOINT = f"{SONAR_URL}/api/issues/search"
SONAR_PRJ_PATH = f'{currentScriptPath}/tmp'

def sonarqube_get_all_issues(project_key=PROJECT_KEY):
    """
    Uses REST to get issues for a project.
    Note: Project name is hardcoded (we don't really care)
    """

    if not API_TOKEN:
        print("[run_sast][ERROR]: No $SONARQUBE_TOKEN env var. Exiting...")
        sys.exit(-3)

    # Make the API call
    response = requests.get(
        API_ENDPOINT,
        auth=(API_TOKEN, ''),
        params={
            'componentKeys': project_key,
            'types': 'VULNERABILITY'
        }
    )

    # Check for HTTP requests errors
    response.raise_for_status()

    # Parse the JSON response
    findings_json = response.json()
    return findings_json

def sonarqube_create_run(tool_name, findings):
    """
    Helper function to create a SARIF run object
    """
    return {
        "tool": {
            "driver": {
                "name": tool_name,
                "semanticVersion": "1.0.0"
            }
        },
        "artifacts": [],
        "results": findings
    }

def sonarqube_map_severity_to_level(severity):
    """
    Helper function to map SonarQube severity to SARIF level
    """
    return {
        "INFO"    : "note",
        "MINOR"   : "note",
        "MAJOR"   : "warning",
        "CRITICAL": "error",
        "BLOCKER" : "error"
    }.get(severity, "none")

def sonarqube_convert_finding_to_sarif_result(finding, components):
    """
    Helper function to convert an individual SonarQube finding to SARIF result format
    """
    # Find the component with the same key as the issue's component
    component = next((c for c in components if c['key'] == finding['component']), None)
    # Construct the artifactLocation from the component details
    artifact_location = {
        "uri": component['path'] if component and 'path' in component else finding['component']
    }

    return {
        "ruleId": finding.get("rule"),
        "level": sonarqube_map_severity_to_level(finding.get("severity")),
        "message": {
            "text": finding.get("message")
        },
        "locations": [{
            "physicalLocation": {
                "artifactLocation": artifact_location,
                "region": {
                    "startLine": finding.get("textRange", {}).get("startLine"),
                    "startColumn": finding.get("textRange", {}).get("startOffset") + 1,  # SARIF columns are 1-based
                    "endLine": finding.get("textRange", {}).get("endLine"),
                    "endColumn": finding.get("textRange", {}).get("endOffset") + 1
                }
            }
        }]
    }

# Main function to convert the SonarQube findings to SARIF
def convert_findings_to_sarif(findings_json):
    components = findings_json.get("components", [])
    findings = [sonarqube_convert_finding_to_sarif_result(issue, components) for issue in findings_json.get("issues", [])]

    sarif_output = {
        "version": "2.1.0",
        "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
        "runs": [sonarqube_create_run("SonarQube", findings)]
    }
    return sarif_output

def run_sonarqube(filename, language=None):
    pureFilename = getJustFilename(filename)
    # 1a. Run Sonarqube
        # [DEV/DEBUG]: sonar-scanner -X -Dsconar.login=$SONARQUBE_TOKEN
    print(f"[run_sast]: \033[1mRunning Sonarqube\033[0m from: {currentScriptPath}/tmp")
    preCmd  = f"cd {currentScriptPath}/tmp"
    cmdSet  = []
    
    if language == 'csharp':
        cmdSet.append("dotnet new console --force")           # initialize dotnet project
        cmdSet.append(f"cp {filename} Program.cs")             # copy over source to default source
        cmdSet.append("dotnet build")                         # build the source 
        cmdSet.append("sonar-scanner")                        # scan the code       
        cmdSet.append("rm -rf Program.cs bin obj tmp.csproj") # Remove build artifacts
    
    for cmd in cmdSet:
        print(f"[run_sast]: Running \033[1m{cmd}\033[0m")
        subprocess.run(f"{preCmd} && {cmd}", shell=True)
    # 1b. Fetch Results as Json and save them
    allFinds_json = sonarqube_get_all_issues()
    tmpFormatFilename = f"{currentScriptPath}/tmp/{pureFilename}.sonarqube_json.temp"
    try:
        with open(tmpFormatFilename, 'w') as f:
            json.dump(allFinds_json, f, indent=4)
    except Exception as e:
        print(f"[run_sast][ERROR] - {e}")
        sys.exit(-2)
    
    # 2. Convert to SARIF
    sonarqube_output_sarif = convert_findings_to_sarif(allFinds_json)
    # filter on filename:
    sonarqube_output_sarif['runs'][0]['results'] = [x for x in sonarqube_output_sarif['runs'][0]['results'] \
                                       if x['locations'][0]['physicalLocation']['artifactLocation']['uri'] == 'Program.cs']
    

    # 3. Save SARIF
    try:
        with open(f'{currentScriptPath}/tmp/{pureFilename}.sonarqube.tmp', 'w') as f:
            json.dump(sonarqube_output_sarif, f, indent=4)
    except Exception as e:
        print(f"[run_sast][ERROR] - {e}")
        sys.exit(-3)


# -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- #
# -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- #
# -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- # -- Bandit -- # 
def run_bandit(filename, language='python'):
    pureFilename = getJustFilename(filename)
    tmpFormatFilename = f"{currentScriptPath}/tmp/{pureFilename}.bandit_json.temp"
    # 1. Run Bandit
    cmd = f"bandit -f json -o {tmpFormatFilename} {filename}"
    print(f"[run_sast]: Running \033[1m{cmd}\033[0m")
    subprocess.run(cmd, shell=True)
    # 2. convert to sarif
    with open(f'{tmpFormatFilename}', 'r') as f:
        bandit_output_json = json.load(f)
        bandit_output_sarif = bandit_to_sarif(bandit_output_json)
    # 3. save sarif format
    with open(f'{currentScriptPath}/tmp/{pureFilename}.bandit.tmp', 'w') as f:
        json.dump(bandit_output_sarif, f)

# -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # 
# -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # 
# -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # -- Semgrep -- # 
def run_semgrep(filename, language=None):
    pureFilename = getJustFilename(filename)
    cmd = f"semgrep --config p/default {filename} --sarif -o {currentScriptPath}/tmp/{pureFilename}.semgrep.tmp"
    print(f"[run_sast]: Running \033[1m{cmd}\033[0m")
    subprocess.run(cmd, shell=True)

def run_gosec(filename, language='go'):
    pureFilename = getJustFilename(filename)
    cmd  = f"cd {currentScriptPath}/tmp && rm *.go 2>/dev/null ; cp {filename} . && "
    cmd += f"gosec -fmt=sarif -out={pureFilename}.gosec.tmp ./..."
    print(f"[run_sast]: Running \033[1m{cmd}\033[0m")
    subprocess.run(cmd, shell=True)
    
# ------- [/SAST TOOLS ] ------- #

function_map = {
    "semgrep"  : run_semgrep,
    "bandit"   : run_bandit,
    "sonarqube": run_sonarqube,
    "gosec"    : run_gosec
}

# ------------------------------ #
def sarif_to_html(filename):
    # Load SARIF results
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"[run_sast]\033[1m[WARN]\033[0m {filename} not produced.")
        data = {}


    # Basic template for HTML output
    template_str = """<ul>    
{% for run in sarif.runs %}
    {% for result in run.results %}
    <li style="text-align: left;">
        <strong>Line:</strong> {{ result.locations[0].physicalLocation.region.startLine }}<br>
        <strong>Rule ID:</strong> {{ result.ruleId }}<br>
        <strong>Message:</strong> {{ result.message.text }}<br>
    </li>
    {% endfor %}
{% endfor %}
</ul>"""

    template = Template(template_str)
    html_output = template.render(sarif=data)
    return html_output

def save_html(html_output, filename_out):
    # Save HTML output to a file
    # Convention: filename_out = filename.tool.sast.html
    with open(filename_out, "w") as html_file:
        html_file.write(html_output)




# ------------------------------ #
def run_all(filename, savePath=f'{currentScriptPath}/tmp'):
    justFilename = filename
    # patch filename
    filename = f"{currentScriptPath}/../snippets/{filename}"
    
    if not os.path.exists(filename):
        print(f"[FileNotFound] {filename}")
        raise FileNotFoundError

    fileLang = getLang(filename)
    toolsToRun = lang2sast.get(fileLang,[])
    
    print(f"{fileLang=} {toolsToRun=}")

    for tool in toolsToRun:
        # run the tool
        function_map[tool](filename, language=fileLang)
        # go through result file
        resultFile = f'{currentScriptPath}/tmp/{justFilename}.{tool}.tmp'
        if os.path.exists(resultFile):
            sarifAsHtml = sarif_to_html(resultFile)
            save_html(sarifAsHtml, f'{savePath}/sast.{tool}.html')
        else:
            # nothing is ever heterogenous :-(
            # sonarqube currently
            if tool not in ['sonarqube']:
                print(f"[run_sast][INFO] {tool} -- {resultFile} not produced." + \
                       "                 Make sure if it's the intended behavior")

def cleanup():
    """
    After running all SAST tools, remove temporary files.
    """
    print("[run_sast] Started cleanup...")
    os.chdir(f'{currentScriptPath}/tmp')

    # Find and remove *.tmp files
    for tmp_file in glob.glob('*.tmp'):
        os.remove(tmp_file)
        print(f"Removed: {tmp_file}")

    # Find and remove *.temp files
    for temp_file in glob.glob('*.temp'):
        os.remove(temp_file)
        print(f"Removed: {temp_file}")

    print("[run_sast] Cleanup done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert SARIF file to HTML")
    parser.add_argument("filename", help="Input filename")
    args = parser.parse_args()
    filename = args.filename
    run_all(filename)
    cleanup()