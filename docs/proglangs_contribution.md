# Adding support for additional programming languages

We'll document this as an example diff of the changes for when when golang was added.

## QRD of needed additions:
1. Specify a lexer for `pygments` to be able to do syntax highlighting for the new programming language (needed since the displayed challenge is raw, pre-highglighted HTML. This is due to dev team's allergy to bloated clientside js)
2. The challenge creation helper script needs to know 2 things about a programming language: 
    1. what file extension corresponds to it
    2. what SAST tools correspond to it
        - how to run those tools (and convert the output to SARIF format, or a simplified mockup that follows SARIF spec)

Now for the changes, in order, for having added golang:

### 1. Correct syntax highlighting in: `barebones_js/utils/pygments_stuff.py`

```python
# ...
        elif prog_lang == 'go':
            lexerClassPath = 'pygments.lexers.GoLexer'
# ...
```

`barebones_js/utils/run_sast.py`

```python
def run_gosec(filename, language='go'):
    pureFilename = getJustFilename(filename)
    cmd  = f"cd {currentScriptPath}/tmp && rm *.go 2>/dev/null ; cp {filename} . && "
    cmd += f"gosec -fmt=sarif -out={pureFilename}.gosec.tmp ./..."
    print(f"[run_sast]: Running \033[1m{cmd}\033[0m")
    subprocess.run(cmd, shell=True)
    
# ------- [/SAST TOOLS ] ------- #

function_map = {
    "gosec"    : run_gosec
}
```


### 2. Mapping files

#### 2.1 File extension: `utils/ext2lang.json`
```json
{
...
    "go": "go",
...
}
```

#### 2.2 SAST Tools needed: `utils/lang2sast.json`
```json
{
...
    "go": ["semgrep", "gosec"],
...
}