# ================================================================================
# sift_engine.py
# The Entry point for the SIFT Test Machine
#
# Author:  Paul Melville
# Created: 25 APR 2023
# ================================================================================
import sys
import time
import subprocess, os
from ast import literal_eval
from collections import deque
from sift_util import *
try:
    import readline
except ImportError:
    import pyreadline as readline

# ================================================================================
# Dictionary of Delimiter Pairs
# ================================================================================
delim_dict = {
    '(': ')',
    '{': '}',
    '[': ']',
    '"': '"',
    "'": "'"
}

# ================================================================================
# Search a string to find the specified begin-delimiter
# ================================================================================
def find_delim(s, delim, start=0):
    # Over before it's begun
    if start < 0:
        return start
    """
    Finds the specified opening delimiter
    skipping over escaped characters and in-quote character

    Parameters:
        s (str): The input string.
        delim (str): The opening delimiter
        start (int): The index of the start of the search

    Returns:
        int: Index of the opening delimiter, or -1 if not found.
    """
    if delim not in delim_dict:
        return -1

    i = start
    while i < len(s):
        c = s[i]
        # Skip escaped characters
        if c == '\\':
            i += 2
            continue
        # Found the opening delimiter!
        if c == delim:
            return i
        if c == "'" or c == '"':
            # Skip over the quoted part
            inner_end = find_delim_match(s, c, i)
            if inner_end == -1:
                return -1
            i = inner_end  # resume scanning after inner match
        i += 1
    return -1  # No match found

# ================================================================================
# Search a string to find the end-delimiter that matches the provided beginning delimiter
# ================================================================================
def find_delim_match(s, delim, start=0):
    # Over before it's begun
    if start < 0:
        return start
    """
    Finds the matching closing delimiter for the given opening delimiter,
    skipping over escaped characters, in-quote character, and respecting nested delimiters.

    Parameters:
        s (str): The input string.
        delim (str): The opening delimiter to match.
        start (int): The index of the opening delimiter in s.

    Returns:
        int: Index of the matching closing delimiter, or -1 if unmatched.
    """
    if delim not in delim_dict:
        return start + 1  # Not a delimiter — signal to skip it

    closing = delim_dict[delim]
    i = start + 1

    inquote = True if delim == '"' or delim == "'" else False

    while i < len(s):
        c = s[i]
        # Skip escaped characters
        if c == '\\':
            i += 2
            continue
        # Found the ending delimiter!
        if c == closing:
            return i

        newquote = True if (delim == '"' and c == "'") or (delim == "'" and c== '"') else False
        if c in delim_dict and (not inquote or newquote):
            inner_end = find_delim_match(s, c, i)
            if inner_end == -1:
                return -1
            i = inner_end  # resume scanning after inner match
        i += 1
    return -1  # No match found

# ================================================================================
var_dict = {}
var_stack = deque()

var_dict["R7"] = 0
var_dict["R6"] = 0
var_dict["R5"] = 0
var_dict["R4"] = 0
var_dict["R3"] = 0
var_dict["R2"] = 0
var_dict["R1"] = 0
var_dict["R0"] = 0

# ================================================================================
def sift_sub(cmdsub):
    # Variable Substitution
    pos = len(cmdsub)
    while pos > 0:
        try:
            pos = cmdsub[0:pos].rindex("$")
        except ValueError:
            # No Replacements Found
            break
        # Escaped Replacement
        if pos > 0 and cmdsub[pos-1] == '\\':
            cmdsub = cmdsub[0:pos-1] + cmdsub[pos:]
            pos -= 2
            continue
        # Non-Escaped Replacement
        nokori = cmdsub[pos:]
        start = pos + 1
        end   = 1
        delim = ""
        if len(nokori) <= 1:
            repl = ""
        else:
            if cmdsub[pos+1] == "{":
                delim = "}"
            if cmdsub[pos+1] == "(":
                delim = ")"
            start += len(delim)
            end = 0
            nokori = cmdsub[start:]
            nokori = nokori.lstrip()
            if len(nokori) < 1:
                repl = ""
            else:
                if delim == "":
                    varname = nokori.split()[0]
                else:
                    varname = nokori.split(delim)[0]
                end += len(varname) + len(delim)
                if varname == "":
                    repl = ""
                else:
                    repl = var_dict.get(varname, "")
                    # print("Sub \"{}\" --> \"{}\"".format(varname, repl))
        cmdsub = cmdsub[0:pos] + repl + ("" if end >= len(nokori) else nokori[end:])

    return cmdsub

# ================================================================================
def replace_delim(cmd_line, delim, vdc):
    """
    Replaces unquoted and unescaped occurrences of `delim` with `vdc` in the input string.
    Quoted regions (single or double) are skipped entirely.
    Escaped delimiters are ignored.
    """
    result = []
    i = 0
    in_quote = None  # None or one of: "'", '"'

    while i < len(cmd_line):
        c = cmd_line[i]

        if c == '\\':
            # Escape sequence: copy next char literally
            result.append(cmd_line[i:i+2])
            i += 2
            continue

        if in_quote:
            result.append(c)
            if c == in_quote:
                in_quote = None  # End of quote
            i += 1
            continue

        if c in ('"', "'"):
            in_quote = c
            result.append(c)
            i += 1
            continue

        if c == delim:
            result.append(vdc)
        else:
            result.append(c)

        i += 1

    return ''.join(result)

# ================================================================================
def sift_repl(cmd_line, vdc, substi_str):
    # Replace all ESC-vdc and also (in-quote vdc) with (substi_str)
    new_cmd_line = ""
    inquote = False
    for idx in range(0,len(cmd_line)):
        # Escape Char?
        if cmd_line[idx] == '\\':
            idx += 1
            if idx < len(cmd_line):
                if cmd_line[idx] == vdc[0]:
                    new_cmd_line += substi_str
                else:
                    new_cmd_line += vdc[0]
                    new_cmd_line += cmd_line[idx]
                continue;

        if inquote:
            if cmd_line[idx] == vdc[0]:
                new_cmd_line += substi_str
                continue;

        # Begin or End Quotes?
        if cmd_line[idx] == '"':
            inquote = True if inquote == False else False

        # Default: copy that characater
        new_cmd_line += cmd_line[idx]
        continue;

    return new_cmd_line

# ================================================================================
def sift_csub(cmd_list, vdc, substi_str):
    # Replace all (substi_str) with (vdc)
    for idx in range(0,len(cmd_list)):
        pcs = cmd_list[idx].split(substi_str);
        cmd_list[idx] = vdc.join(pcs)

    return cmd_list

# ================================================================================
module_list = {}

module_list["bash"]    = " "
module_list["dos"]     = " "
module_list["py"]      = "python3"
module_list["harvest"] = "harvest"
module_list["hunt"]    = "hunt"
# ================================================================================
def sift_engine(layer, cmd_line):
    global var_dict

    # print(f"SIFT Start Layer {layer}: {cmd_line}")
    # Prep the Engine
    if layer == 0:
        # Init the SIFT Data Structures
        # TBD: Open the CommandLog
        print("========================================")
        print("SIFT Engine Main Entry Point")
        print("========================================")

    # Create the Prompt String for this Layer
    prompt = ">:"
    for i in range(0,layer):
        prompt += ":"
    prompt += "SIFT" + str(layer) + "> "

    # Fixup the CmdLine
    vdc   = "=NEW_CMD="
    # Step 1: Replace instances of <newline> with our VDC (Virtual Delimiter of Commands)
    cmd_line = cmd_line.replace('\n', f" {vdc} ")
    # print(f"CMD_LINE:\n{cmd_line}\n------------->EOC")

    # Step 2: Replace un-quoted and un-escaped ";" with our VDC
    cmd_line = replace_delim(cmd_line, ';', vdc)

    # Step 3: Split (per VDC) into individual single-line commands
    cmd_list = cmd_line.split(vdc)

    # Loop thru the commands, then interactively
    cmd_num = 0
    cmd="mada da yo"
    lineProc = True
    while lineProc:
        # Command-line commands first
        if len(cmd_list) > cmd_num:
            cmd = cmd_list[cmd_num]
            cmd_num += 1
        else:
            # Take Input interactively from the user
            cmd = input(prompt)

        # print("Spl1tCmd: \"" + cmd + "\"")
        cmd = cmd.lstrip().strip()
        # print("Str1pCmd: \"" + cmd + "\"")
        if len(cmd) == 0:
            # 'tis an Empty Command
            # print("\t\tEmpty Cmd")
            continue

        # Variable Substitution
        cmd = sift_sub(cmd)

        # print("Spl2tCmd: \"" + cmd + "\"")
        cmd = cmd.lstrip().strip()
        # print("Str2pCmd: \"" + cmd + "\"")
        if len(cmd) == 0:
            # 'tis an Empty Command
            # print("\t\tEmpty Cmd")
            continue

        procCmd = True
        # print("Here we go!")
        while procCmd:
            procCmd = False
            # TBD: Log the Command in the CommandLog
            # print("...again...!")

            if cmd[0] == '#':
                # 'tis a Comment!
                continue

            if match_cmd(cmd, "quit"):
                # 'tis a request to exit
                lineProc = False
                break

            if match_cmd(cmd, "exit"):
                # 'tis a request to exit
                lineProc = False
                break

            if match_cmd(cmd, "nop"):
                # 'tis a request to do-nothing-get-paid
                continue

            # Loadable Modules (like: bash, gob, blink, wisp, laugh, gnob, etc)
            cwords = cmd.split()
            module = cwords[0]
            if module in module_list.keys():
                pred = grab_predic8(cmd, module)
                cwords = pred.split()
                default_shell = "dos" if os.name == 'nt' else "bash"
                if module != default_shell:
                    cwords = [module_list[module]] + cwords
                # print("\tCMD:\t" + cwords[0])
                # print("\tARG:\t" + " ".join(cwords[1:]))
                try:
                    if default_shell == "dos":
                        cmd = " ".join(cwords)  # Windows CMD wants a string
                        # print(f"DOSCMD: \"{cmd}\"")
                        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                    else:
                        result = subprocess.run(cwords, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

                    var_dict["ret"] = str(result)
                    var_dict["subproc"] = result.stdout.decode('utf-8')
                    print(var_dict["subproc"], end='')
                except IOError: 
                    print("Error: Failed to Run Sub-Process \"" + cwords[0] + "\" -- command not found")
                    var_dict["ret"] = "CmdNotFound"
                    var_dict["subproc"] = ""
                continue

            pred = grab_predic8(cmd, "sleep")
            if pred != "":
                dura = int(pred)
                dura = dura / 1000.0
                # print("Sleeping for " + str(dura) + "s")
                time.sleep(dura)
                continue

            if match_cmd(cmd, "echo"):
                pred = grab_predic8(cmd, "echo")
                if pred != "":
                    print(pred)
                continue

            pred = grab_predic8(cmd, "file")
            if pred != "":
                spread = pred.split()
                if len(spread) < 2:
                    continue
                fname = spread[0].strip()
                foper = spread[1].strip()
                npos  = pred.find(fname) + len(fname)
                pred  = pred[npos:]
                npos  = pred.find(foper) + len(foper)
                pred  = pred[npos:].strip() + "\n"
                try:
                    if foper == "clear":
                        open(fname, 'w')
                    if foper == "write":
                        if len(spread) < 3:
                            continue
                        with open(fname, 'a') as file:
                            file.write(pred)
                    if foper == "read":
                        with open(fname, 'r') as file:
                            alltxt = file.read()
                            var_dict["file_read"] = alltxt
                except IOError: 
                    print("Error: Text File \"" + fname + "\" not found")
                continue

            pred = grab_predic8(cmd, "prompt")
            if pred != "":
                try:
                    resp = input(pred + ": ")
                    var_dict["response"] = resp
                except KeyboardInterrupt:
                    print("\nIgnoring Non-Response")
                    var_dict["response"] = ""
                continue

            pred = grab_predic8(cmd, "var")
            if pred != "":
                varr = pred.split("=")[0]
                vall = grab_predic8(pred, varr, "=")
                if vall == "XXX":
                    if var_dict.get(varr, None) != None:
                        del var_dict[varr]
                # Assign varr from an eval sub-expression
                elif grab_predic8(vall, "eval", "("):
                    subcmd = f"{vall} {vdc} quit"
                    sift_engine(layer+1, subcmd)
                    var_dict[varr] = var_dict.get("result", "0")
                else:
                    var_dict[varr] = vall
                continue

            # This is mainly for debug purposes
            pred = grab_predic8(cmd, "delim")
            if pred != "":
                delim = pred.split("=")[0]
                linea = grab_predic8(pred, delim, "=")
                begin = find_delim(linea, delim)
                enddd = find_delim_match(linea, delim, begin)
                print(f"Begin @{begin:3}  End @{enddd:3}")
                print(f"{linea}")
                if begin >= 0 and enddd >= 0:
                    print(''.join('^' if i in (begin, enddd) else ' ' for i in range(max(begin, enddd) + 1)))
                continue

            pred = grab_predic8(cmd, "module")
            if pred != "":
                modd = pred.split("=")[0]
                nomm = grab_predic8(pred, modd, "=")
                if nomm == "XXX":
                    if module_list.get(modd, None) != None:
                        del module_list[modd]
                else:
                    module_list[modd] = nomm
                continue

            if match_cmd(cmd, "push"):
                pred = grab_predic8(cmd, "push")
                var_stack.append(pred)
                continue

            if match_cmd(cmd, "pop"):
                pred = grab_predic8(cmd, "pop")
                try:
                    vall = var_stack.pop()
                except IndexError:
                    vall = ""
                if pred != "":
                    var_dict[pred] = vall
                continue

            pred = grab_predic8(cmd, "jump")
            if pred != "":
                jpoint = pred.split()[0]
                jhunt = "LABEL " + jpoint
                found = False
                # print("Hunting for " + jhunt)
                if jpoint != "":
                    totallen = len(cmd_list)
                    # print("We have {} Lines to Check".format(totallen))
                    for idx in range(0,totallen):
                        # print("Looking for \"{}\" in \"{}\"".format(jhunt, cmd_list[idx]))
                        if jhunt in cmd_list[idx]:
                            # print("Jumping to Label: " + jpoint)
                            cmd_num = idx
                            found = True
                            break
                if not found:
                    print("FAILED to Find Label: \"" + jpoint + "\"")
                continue

            pred = grab_predic8(cmd, "call")
            if pred != "":
                jpoint = pred.split()[0]
                jhunt = "LABEL " + jpoint
                found = False
                var_dict["ret"] = ""
                # print("Hunting for " + jhunt)
                if jpoint != "":
                    totallen = len(cmd_list)
                    # print("We have {} Lines to Check".format(totallen))
                    for idx in range(0,totallen):
                        # print("Looking for \"{}\" in \"{}\"".format(jhunt, cmd_list[idx]))
                        if jhunt in cmd_list[idx]:
                            # Push the Return-Address for Later
                            var_stack.append(cmd_num)
                            # Push the Temp Regs
                            var_stack.append(var_dict["R0"])
                            var_stack.append(var_dict["R1"])
                            var_stack.append(var_dict["R2"])
                            var_stack.append(var_dict["R3"])
                            var_stack.append(var_dict["R4"])
                            var_stack.append(var_dict["R5"])
                            var_stack.append(var_dict["R6"])
                            var_stack.append(var_dict["R7"])

                            # print("Calling Sub at Label: " + jpoint)
                            cmd_num = idx
                            found = True
                            break
                if not found:
                    print("FAILED to Find Label: \"" + jpoint + "\"")
                continue

            if match_cmd(cmd, "return"):
                if layer == 0:
                    continue
                pred = grab_predic8(cmd, "return")
                if pred != "":
                    var_dict["ret"] = pred
                # Pop the Temp Regs
                var_dict["R7"] = var_stack.pop()
                var_dict["R6"] = var_stack.pop()
                var_dict["R5"] = var_stack.pop()
                var_dict["R4"] = var_stack.pop()
                var_dict["R3"] = var_stack.pop()
                var_dict["R2"] = var_stack.pop()
                var_dict["R1"] = var_stack.pop()
                var_dict["R0"] = var_stack.pop()
                # Pop the Return-Address ... and Jump to that Command-Number
                cmd_num = var_stack.pop()
                continue

            pred = grab_predic8(cmd, "eval", "(")
            if pred != "":
                try:
                    endo = find_delim_match(pred, "(")
                except ValueError:
                    print(f"Malformed Expression: {pred}")
                    continue
                pred = pred[:endo]
                pred = pred.lstrip().rstrip()
                # print(f"Requested Evaluation: ({pred})")
                clean_str = True
                skipstr = pred
                inquote_single = False
                inquote_double = False
                for idx in range(0,len(skipstr)):
                    if pred[idx] == '"':
                        inquote_double = False if inquote_double else True
                    if inquote_double:
                        continue
                    if pred[idx] == "'":
                        inquote_single = False if inquote_single else True
                    if inquote_single:
                        continue
                    if pred[idx] in "_ghjkmpqsuvwyzGHIJKLMNOPQRSTUVWYZ":
                        print("Expression Contains \"{}\": {}".format(pred[idx],pred))
                        print("Will not Evaluate")
                        clean_str = False
                        break
                if not clean_str:
                    continue

                # print("Evaluating ({})".format(pred))
                try:
                    rez = eval(pred)
                    # print(f"EVAL({pred}) --> \"{rez}\"")
                except SyntaxError:
                    print("Bad Syntax!")
                    rez = "NULL"
                except ValueError:
                    print("Bad Value!")
                    rez = "NULL"
                except NameError:
                    print("Bad Name!")
                    rez = "NULL"
                if layer == 0:
                    print("Result is: {}".format(rez))
                var_dict["result"] = str(rez)
                continue

            pred = grab_predic8(cmd, "if", "(")
            if pred != "":
                try:
                    endo = find_delim_match(pred, "(")
                except ValueError:
                    print(f"Malformed Expression: {pred}")
                    continue
                nokori = pred[endo+1:]
                pred = pred[:endo]
                pred = pred.lstrip().rstrip()
                #print("\t\tEVALUATING: " + pred)
                subcmd = f"eval( {pred} ) {vdc} quit"
                sift_engine(layer+1, subcmd)
                if var_dict.get("result", "False") == "False":
                    continue
                elif var_dict.get("result", "0") == "0":
                    continue
                elif var_dict.get("result", "0.0") == "0.0":
                    continue
                cmd = nokori.lstrip()
                #print("\t\tNEW-CMD: " + cmd)
                procCmd = True
                # print("CONDITIONAL Cmd: \"{}\"".format(cmd))
                continue

            if match_cmd(cmd, "layer"):
                pred = grab_predic8(cmd, "layer")
                sift_engine(layer+1, pred)
                continue

            fyle = ""
            pred = grab_predic8(cmd, "script")
            if pred != "":
                # See if the command introduces the script file
                fyle = pred.split()[0]
            if fyle == "":
                # See if the command is a script file
                fyle = cmd.split()[0]
            if fyle != "":
                # We are trying a script file!
                try:
                    # print("Opening Script File \"" + fyle + "\"")
                    with open(fyle, 'r') as file:
                        pred = file.read()
                        # print(f"FILE READ:\n{pred}\n------------->EOF")
                        pred += f"\nquit"
                except IOError:
                    print("Error: Script File \"" + fyle + "\" not found")
                    continue

                # Use SIFT to execute the Script!
                sift_engine(layer+1, pred)
                # print("Closing Script File \"" + fyle + "\"")

            # End-of-the-Line!   We have no more logic to apply to the parsing
            continue


    if layer > 0:
        # print("Exiting Layer " + str(layer))
        return
    else:
        print("========================================")
        print("Exiting SIFT Engine")
        print("========================================")


# ================================================================================
if __name__ == '__main__':
    # print(sys.argv)
    cmd_line = ""
    if len(sys.argv) > 1:
        # print(sys.argv[1:])
        # Get the list of commands
        cmd_line=' '.join(sys.argv[1:])
        # print("CmdLine: \"" + cmd_line + "\"")
    sift_engine(0, cmd_line)

# ================================================================================
