#!/usr/bin/env python3
import re
import sys
from collections import OrderedDict

# A simple, quick & dirty script to parse GamCommands.txt and
# produce HTML with parameter references in commands linked to their
# definitions.
# 
# We expect the following grammar:
# 
#     ^gam.*              Beginning of a command
#     <(.*?)>\s+::=       Beginning of a parameter BNF production
# 
# Input lines immediately following a command or parameter are
# accumulated until encountering a blank line or the next command or
# parameter.  This is implemented as a state machine.
# 
# In the output HTML, every parameter definition is given an id=
# attribute (__x where x is the parameter name) and references in
# commands and RHS of parameter productions are links pointing to the
# definition.
# 
# Input is syntax-checked to verify matching angle-brackets. If 
# an entry fails this test it is discarded and a message is written 
# to stderr.
# 
# There are also 3 special cases handled separately since they don't
# fit this grammar.  See 'specialCases' below.
# 
# If a parameter (BNF production) duplicates one we've already seen, we
# ignore it, and if it isn't identical to the existing one we write a
# message to stderr.
# 
# Written with python 3.7, explaining non-use of lookahead/lookbehind
# 
# Typical usage:
# 
#     python mkGamRef.py GamCommands.txt > GamCommands.html
# 

reCommand     = re.compile(r'gam ')             # Start of command
reProduction  = re.compile(r'<(.*?)>\s+::=')    # Start of parameter BNF production
reBlankLine   = re.compile(r'\s*')              # Totally blank line
reWhitespace  = re.compile(r'\s+')              # To detect continuations for HTML <br/>
reProdRef     = re.compile(r'<(.*?)>')          # Cross-reference to a parameter 
reBrackets    = re.compile(r'[<>]')             # For counting brackets
reBadLink1    = re.compile(r'[/a-zA-Z]+>')      # Pin down missing opening bracket
reBadLink2    = re.compile(r'<[/a-zA-Z]+')      # Pin down missing closing bracket

# Special cases of input that get "fixed" on input because
# they don't follow the grammar used everywhere else
specialCases  = [
    [re.compile(r'<(Number in range )(\d+)-(\d+)>'),    r'&lt;\1\2-\3&gt;'],
    ['<|<=|>=|>|=|!=',                                  '&lt; | &lt;= | &gt;= | &gt; | = | !='], 
    ['<RRULE, EXRULE, RDATE and EXDATE line>',          '&lt;RRULE, EXRULE, RDATE and EXDATE line&gt;'] ]

# List of gam commands. Each entry is a list of input lines
commands    = []

# OrderedDict of parameter BNF productions
#    key:   non-terminal name
#    value: List of input lines
productions = OrderedDict()

# Simple HTML wrapper
prefix = '''\
<html>
    <head></head>
    <body style="font-size:large; font-family:monospace">
    <p><a href="#_commands">Commands</a>
    <p><a href="#_parameters">Parameters</a>
'''

suffix = '''\
    </body>
</html>
'''

# Examine an input line and return a token type, extracted
# production key (if this is the first line of a production)
# and the line text, all as a tuple
#    Token Types: 
#       0 - Blank line
#       1 - First line of gam command
#       2 - First line of BNF parameter production
#       3 - Everything else
def examine(line):  
    if reBlankLine.fullmatch(line):
        return (0, '', '')
    
    m = reCommand.match(line)
    if m:
        return (1, '', line)

    m = reProduction.match(line)
    if m:
        return (2, m.group(1), line)

    return (3, '', line)

# Save the current command or production
# Detect duplicate BNF productions and write an error message
# if not identical to the one already on file
def save(state,key,data):
    global commands, productions
    if state==1: 
        commands += [data]
    elif state ==2:
        if key in productions:
            if data == productions[key]:
                #sys.stderr.write(f"Identical duplicate production {key} ignored\n")
                pass
            else:
                sys.stderr.write(f"Conflicting duplicate production {key} ignored\n")
        else:
            productions[key] = data

# Detect and fix special cases
def fixSpecialCases(line):
    for c in specialCases:
        # c is a tuple (search, replacement)
        # search can be a re.Pattern, in which case replacement is a regex sub with backreferences
        # search can be a string, in which case replacement is a direct substitution
        if isinstance(c[0], re.Pattern):
            if c[0].search(line): 
                line = c[0].sub(c[1],line)
        else:
            pos = line.find(c[0])
            if pos >= 0:
                line = line[:pos] + c[1] + line[pos+len(c[1]):]
    return line
    
# Write the HTML for one complete command or production,
# generating the cross-references from command parameters to
# the parameter definitions (the BNF productions)
def resolve(data,id=None):
    if id:
        result = f'<div id="__{id}" style="padding:12px; padding-left:100px; text-indent:-90px">'
    else:
        result = f'<div style="padding:12px; padding-left:100px; text-indent:-90px">'

    for line in data:
        if reWhitespace.match(line):
            result += "<br/>"
        result += reProdRef.sub(r'<a href="#__\1">&lt;\1&gt;</a>', line)

    result += "</div>"
    return result

# Syntax check an input line
def validate(line):
    
    # Check bracket matching/nesting (no nesting allowed)
    blist = reBrackets.findall(line)
    depth = 0
    nnest = False
    for c in blist:
        if   c == '<':  depth += 1
        elif c == '>':  depth -= 1
        if depth > 1: nnest = True
        
    if depth != 0 or nnest: 
        return False
    
    # Look for bracket syntax errors
    for m in reBadLink1.finditer(line):
        if m.start() == 0 or line[m.start()-1] != '<':   
            return False
            
    for m in reBadLink2.finditer(line):
        if m.end() >= len(line) or line[m.end()] != '>': 
            return False
    
    return True

# Simple Finite State Machine to parse GamCommands.txt
#
#                  C u r r e n t   S t a t e
#                   0          1          2
# Input Token     Start       gam       <BNF>
# ------------    -----       ---       -----
# 0 empty Line      -         s0         s0 
# 1 gam            1+         s1+        s1+
# 2 <BNF>          2+         s2+        s2+
# 3 all other       -          1+         2+
#               
# Key:           
#    digit = next state
#    s     = current item done, save it
#    +     = Add current line to buffer
#    -     = no-op
#

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.stderr.write("Single argument must be the input file name\n")
        sys.exit(1)
        
    fname = sys.argv[1]
    state  = 0  # Current FSM State
    buffer = [] # Work are in which we build an item
    lnum   = 0
    key    = ''
    
    with open(fname,"r") as infile:
        for line in infile:
            lnum += 1
            line = fixSpecialCases(line.rstrip())

            if not validate(line):
                sys.stderr.write(f"Unbalanced angle-brackets in line {lnum}\n")
            else:
                token,k,line = examine(line)
                
                if state == 0:
                    if token==1 or token==2:
                        buffer = [line]
                        if token==2: key = k
                        state = token
                else:
                    if token < 3:
                        save(state,key,buffer)
                        buffer = [line]
                        if token==2: key = k
                        state  = token
                    else:
                        buffer.append(line)

        # On EOF, close out the last unclosed item if there is one
        if state > 0:
            save(state,key,buffer)

    # Write out the HTML
    print(prefix)
    
    print('<h1 id="_commands">Commands</h1>')
    for v in sorted(commands):
        print(resolve(v))
        
    print('<h1 id="_parameters">Parameters</h1>')
    for k,v in productions.items():
        print(resolve(v,k))

    print(suffix)

