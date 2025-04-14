# Command Line Parsing
- [Linux and MacOS](#linux-and-macos)
- [Windows Command Prompt](#windows-command-prompt)
- [Windows PowerShell](#windows-powershell)
- [List quoting rules](#list-quoting-rules)
- [Queries example](#queries-example)

## Linux and MacOS

When entering `gam csv` commands, you should enclose references to CSV file headers in `"`; e.g., `name "~name"`.

In bash, if an argument contains a `~`, `|`, `>`, or `<`, you must enclose the argument in `"`; e.g., `name "Test|Group"`.

In zsh, if an argument contains a `~`, `|`, `!`, `>`, or `<`, you must enclose the argument in `'`; e.g., `name 'Test|Group'`.

To embed a `'` in a string enclosed in `"`, enter `'`; `name "Test'Group"`.

To embed a `"` in a string enclosed in `'`, enter `"`; `name 'Test"Group'`.

To embed a `'` in a string enclosed in `'`, enter `'\''`; `name 'Test'\''Group'`.

To embed a `"` in a string enclosed in `"`, enter `\"`; `name "Test\"Group"`.

Linux and MacOS do not recognize smart or curly quotes, `“` and `”`, they can not be used to enclose arguments.

## Windows Command Prompt

Command Prompt does not recognize smart or curly quotes, `“` and `”`, they can not be used to enclose arguments.

Command Prompt does not recognize single quotes, `'`, they can not be used to enclose arguments.

To embed a `'` in a string enclosed in `"`, enter `'`; `name "Test'Group"`.

To embed a `"` in a string enclosed in `"`, enter `\"`; `name "Test\"Group"`.

## Windows PowerShell

In PowerShell, if you want an empty string argument, you must enter: ``` `"`" ```

PowerShell does not recognize smart or curly quotes, `“` and `”`, they can not be used to enclose arguments.

To embed a `'` in a string enclosed in `"`, enter `'`; `name "Test'Group"`.

To embed a `"` in a string enclosed in `"`, enter ``` `" ```; ```name "Test`"Group"```.

To embed a `'` in a string enclosed in `'`, enter `''`; `name 'Test''Group'`.

To embed a `"` in a string enclosed in `'`, enter `\"`; `name 'Test\"Group'`.

## List quoting rules
Items in a list can be separated by commas or spaces; if an item itself contains a comma, a space or a single quote, special quoting must be used.
Typically, you will enclose the entire list in double quotes and quote each item in the list as detailed below.

- Items, separated by commas, without spaces, commas or single quotes in the items themselves
   * ```"item,item,item"```
- Items, separated by spaces, without spaces, commas or single quotes in the items themselves
   * ```"item item item"```
- Items, separated by commas, with spaces, commas or single quotes in the items themselves
   * ```"'it em','it,em',\"it'em\""``` - Linux, MacOS, Windows Command Prompt
   * ```"'it\ em','it,em',`"it\'em`""``` - Windows Power Shell
- Items, separated by spaces, with spaces, commas or single quotes in the items themselves
   * ```"'it em' 'it,em' \"it'em\""``` - Linux, MacOS, Windows Command Prompt
   * ```"'it\ em' 'it,em' `"it\'em`""``` - Windows Power Shell

Typical places where these rules apply are lists of OUs and Contact Groups.

## Queries example
### Linux and MacOS
```
gam print users queries "\"orgUnitPath='/Students/Lower School/2027'\",\"orgUnitPath='/Students/Lower School/2028'\""
```

### Windows Command Prompt
```
gam print users queries "\"orgUnitPath='/Students/Lower School/2027'\",\"orgUnitPath='/Students/Lower School/2028'\""
```

### Windows Power Shell
```
gam print users queries "`"orgUnitPath=\'/Students/Lower\ School/2027\'`",`"orgUnitPath=\'/Students/Lower\ School/2028\'`""
```
