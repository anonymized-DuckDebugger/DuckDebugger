# Contribution Guide: Challenge Snippets

To add your own challenges into the platform, you need to do two things:

1. Add a code snippet into `barebones_js/snippets`
  -  The only difference from _"normal"_ code is that the snippets need to include some comments that follow a special formatting (explained below. it's easy, pinky promise!).
2. Use the provided helper script to do the rest of the magic for you:
```bash
cd barebones_js/utils
./genChalYaml.py [name_of_your_snippet_file] [desired display name for the challenge]
```

## Simple Solution Comments

**Dummy code snippet with vulnerabilities:**

```c
L1   int x = 3;
L2   char str[50]; // <normal comment>
L3   gets(str); //!! <solution comment>
```

### Breakdown of the possible lines of code:

* **L1**: "normal" line of code, no vulnerability.
* **L2**: same as L1. *Normal comments* can be included in your snippet. Players will also see them within the snippet.
* **L3**: vulnerable line of code. Comments that start with `!!` are part of the **intended solution**. Players see all solution comments after they "solve" the challenge.

> **Note:** We use `//` in pseudocode for comments. Adjust your comment symbol for the language of your snippet.
> Example for Python:
>
> ```python
> x = 3
> s = input()  # <normal comment>
> eval(s)  #!! <solution comment>
> ```

---

### What the user sees when playing the challenge:

```c
L1   int x = 3;
L2   char str[50]; // <normal comment>
L3   gets(str);
```

When the user solves the challenge, the `<solution comment>` will be displayed alongside **L3**.

**Solution comments support Markdown formatting** (links, bold, code, etc.) and render nicely for the player.

Example solution comment (excluding leading `//!!`):

```text
dummy solution text about vulnerability [link text](http://link.address)
```

---

## Complex Solution Comments

In addition to simple text, solution comments can include optional **fields** for richer information.

**Example:**

```c
//!! comment text @@NUMS 1 2 5-9 +1 -2 @@KWORDS kw1 kw2 kw3
```

### Special Fields

* **`@@NUMS`**
  Other line numbers the comment applies to.

  * Supports absolute (`1 2 5-9`) and relative (`+1 -2`) references.
  * Useful for vulnerabilities where multiple comment locations make sense.

* **`@@KWORDS`**
  Keywords to assess the solution, matched by regex.

  * A player must match at least one keyword.
  * Example: for an injection vulnerability, use `inject` and `input`.

---

### Summary for Complex Comments

1. All fields are optional and order does not matter.
2. Values are **space-separated** (no commas or other separators).

---

## Custom Tags

General structure of a solution comment:

```text
'comment text @@FIELD1 f1_val1 f1_val2 @@FIELD2 f2_val1 @@FIELD3 f3_val1 f3_val2'
```

* You can define **custom fields** (any name except reserved ones).
* Reserved names: `KWORDS`, `NUMS`.
* All other field names are allowed and unlimited.
* Each field can have multiple values, all space-separated.

### Why Custom Tags?

* Tag bugs based on internal guidelines or policies.
* Cluster vulnerabilities for data analysis.
* Useful for analytics/training with the **DuckDebugger** (to be open-sourced).

---

## Final Notes and TL;DR Summary

Recap of a dummy code snippet with vulnerabilities:

```c
int x = 3;
char str[50]; // <normal comment>
gets(str); //!! <solution comment>
```

- **Note 1:** No need for `<` and `>` in comments. 
- **Note 2:** Replace `//` with the comment symbol of the programming language in your snippet.
- **Note 3:** You can use `[links](https://written.in.markdown)` in your solution comments.
- **Note 4:** The `@@NUMS` and `@@KWORDS` fields are optional -- don't bother with them unless you really feel like it. This contradicts the initial "simple convention" request, but we promise you that the backend can take it, out-of-the box, and your extra annotations wouldn't be in vain.
- **Note 5**:
    - Values for each tag are **space-separated** only.
    - All fields are optional.
    - No fixed order -- you can use one, many, or none.

