#!/usr/bin/env python3

from   pygments.formatters import HtmlFormatter
from   pygments.lexers     import guess_lexer
from   pygments            import highlight
import importlib
import sys
import re
import os

DEBUG       = False
scriptDir   = os.path.dirname(os.path.abspath(__file__))

commentSymbol ={ # Leading symbol for comments
    'python'     : '##!!',
    'csharp'     : '//!!',
    'c'          : '//!!',
    'cplusplus'  : '//!!',
    'go'         : '//!!',
    'java'       : '//!!',
    'javascript' : '//!!',
}

def extract_comments_and_clean_source(source_code, commentMarker="//!!"):
    # Dictionary to store line number and comment
    comments = {}

    # List to store lines without comments
    cleaned_lines = []

    # Split the source code into lines
    lines = source_code.split('\n')

    # Regular expression to match comments. Escape marker for regex (i.e. # -> \\# )
    comment_pattern = re.compile(rf'{re.escape(commentMarker)}(\s*.*)')

    # Iterate over the lines, search for comments, and clean the source code
    for line_number, line in enumerate(lines, start=1):
        match = comment_pattern.search(line)
        if match:
            # Extract the comment and add it to the dictionary
            comments[line_number] = match.group(1).strip()
            # Remove the comment from the line
            cleaned_line = comment_pattern.sub("", line).rstrip()
            cleaned_lines.append(cleaned_line)
        else:
            cleaned_lines.append(line)

    # Join the cleaned lines back into a single string
    cleaned_source_code = '\n'.join(cleaned_lines)

    return comments, cleaned_source_code

def highlightHtml(input_filename, prog_lang=None):
    try:
        with open(f'{scriptDir}/../snippets/{input_filename}', 'r') as source_file:
            source_code = source_file.read()
            solution_comments, source_code = extract_comments_and_clean_source(source_code, commentMarker=commentSymbol[prog_lang])
    except FileNotFoundError:
        print(f"Error: File {input_filename} not found.")
        sys.exit(1)

    # Define the lexer and formatter
    if not prog_lang:
        print("[pygments_stuff] Specify the language! We're gonna do a guess now.")
        lexer = guess_lexer(source_code)
    else:        
        if prog_lang == 'csharp':
            lexerClassPath = 'pygments.lexers.dotnet.CSharpLexer'
        elif prog_lang == 'python':
            lexerClassPath = 'pygments.lexers.PythonLexer'
        elif prog_lang == 'go':
            lexerClassPath = 'pygments.lexers.GoLexer'
        elif prog_lang == 'java':
            lexerClassPath = 'pygments.lexers.JavaLexer'
        elif prog_lang == 'javascript':
            lexerClassPath = 'pygments.lexers.JavascriptLexer'
        elif prog_lang == 'c':
            lexerClassPath = 'pygments.lexers.CLexer'
        elif prog_lang == 'cplusplus':
            lexerClassPath = 'pygments.lexers.CppLexer'
        # elif ...:
        #      #add other languages here
        
        else:
            lexerClassPath = None
        try:
            module_name, class_name = lexerClassPath.rsplit('.', 1)
            # Dynamically import the module
            module = importlib.import_module(module_name)
            # Get the class from the module
            dynamic_class = getattr(module, class_name)
            # create dynamic instance of class
            lexer = dynamic_class()
            print(f"[pygments_stuff] Lexer: {module_name}.{class_name}") 
        except ImportError as e:
            print(f"Error importing {module_name}: {e}")

    formatter = HtmlFormatter(style='xcode')

    # Perform syntax highlighting
    highlighted_code = highlight(source_code, lexer, formatter)
    style_defs       = formatter.get_style_defs()

    return (highlighted_code, style_defs, solution_comments)

def saveCodeAsHtml(highlighted_code, style_defs, input_filename='RENAME_ME', dryRun=False, savePath=None, update=False):
    # Generate the HTML page (deprecated, we extract highlighted code later)
    html_page = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Highlighted Python Code</title>
        <style type="text/css">
            {style_defs}
        </style>
    </head>
    <body>
        {highlighted_code}
    </body>
    </html>
    """

    # Split the highlighted code into individual lines
    highlighted_code = highlighted_code.split("<pre>")[-1].split("</pre>")[0]
    # print(highlighted_code)

    # Save the HTML page to a file, make sure filenames are unique
    output_filename = f"{input_filename.split('/')[-1]}.rendered"

    if not savePath:
        savePath = f'{scriptDir}/tmp' # save to tmp
    else:
        savePath = f"{savePath}/{output_filename}"
    
    if not update:
        while os.path.exists(savePath): # append _'s if the file existed before (good for prototyping)
            savePath += "_"

    with open(savePath, 'w') as html_file:
        html_file.write(highlighted_code)
        if __name__ == '__main__' or DEBUG==True:
            print(f"Syntax highlighted HTML snippet saved as:\n {savePath}\n\n")
        return 0
    

def main():
    if len(sys.argv) != 2:
        print("Usage: python highlight.py basic.py")
        sys.exit(1)

    input_filename = sys.argv[1]
    (highlightedCode, style) = highlightHtml(input_filename)
    saveCodeAsHtml(highlightedCode, style, input_filename)

if __name__ == '__main__':
    main()
