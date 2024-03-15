# ================================================================================
# sift_engine.py
# The Entry point for the Test machine for
# the Rules Engine for the Game of Sifteyond
#
# Author:  Paul Melville
# Created: 25 APR 2023
# ================================================================================
import sys
import time
import readline
import subprocess
from ast import literal_eval
from collections import deque
from sift_util import *

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

module_list["bash"] = "bash"
module_list["py"]   = "python3"
module_list["hunt"] = "hunt"
# ================================================================================
def sift_engine(layer, cmd_line):
    global var_dict

    # print("SIFT Start Layer " + str(layer) + ": " + cmd_line)
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

    # Replace all ("\;") and also (in-quote ";") with (".SEMI.")
    vdc = "cmd=="
    repl_str = "CMD_EQ"
    cmd_line = sift_repl(cmd_line, vdc, repl_str)
    cmd_list = cmd_line.split(vdc)
    # For each command in the list, replace (repl_str) with (vdc)
    cmd_list = sift_csub(cmd_list, vdc, repl_str)

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

        # print("SplitCmd: \"" + cmd + "\"")
        cmd = cmd.lstrip().strip()
        # print("StripCmd: \"" + cmd + "\"")
        if len(cmd) == 0:
            # 'tis an Empty Command
            # print("\t\tEmpty Cmd")
            continue

        # Variable Substitution
        cmd = sift_sub(cmd)

        # print("SplitCmd: \"" + cmd + "\"")
        cmd = cmd.lstrip().strip()
        # print("StripCmd: \"" + cmd + "\"")
        if len(cmd) == 0:
            # 'tis an Empty Command
            # print("\t\tEmpty Cmd")
            continue

        procCmd = True
        while procCmd:
            procCmd = False
            # TBD: Log the Command in the CommandLog

            if cmd[0] == '#':
                # 'tis a Comment!
                if layer > 0:
                    print(cmd)
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
                if module != "bash":
                    cwords = [module_list[module]] + cwords
                # print("\tCMD:\t" + cwords[0])
                # print("\tARG:\t" + " ".join(cwords[1:]))
                try:
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
                print("Sleeping for " + str(dura) + "s")
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
                else:
                    var_dict[varr] = vall
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
                            print("Jumping to Label: " + jpoint)
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

                            print("Calling Sub at Label: " + jpoint)
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
                    endo = pred.rindex(")")
                except ValueError:
                    print("Malformed Expression: {}".format(pred))
                    continue
                pred = pred[:endo]
                pred = pred.lstrip().rstrip()
                # print("Requested Evaluation: ({})".format(pred))
                clean_str = True
                skipstr = pred
                inquote = False
                for idx in range(0,len(skipstr)):
                    if pred[idx] == '"':
                        inquote = True if inquote == False else False
                    if inquote:
                        continue
                    if pred[idx] in "_ghjklmpqsuvwyzGHIJKLMNOPQRSTUVWYZ":
                        print("Expression Contains \"{}\": {}".format(pred[idx],pred))
                        print("Will not Evaluate")
                        clean_str = False
                        break
                if not clean_str:
                    continue

                # print("Evaluating ({})".format(pred))
                try:
                    rez = eval(pred)
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
                    endo = pred.rindex(")")
                except ValueError:
                    print("Malformed Expression: {}".format(pred))
                    continue
                nokori = pred[endo+1:]
                pred = pred[:endo]
                pred = pred.lstrip().rstrip()
                #print("\t\tEVALUATING: " + pred)
                subcmd = "eval( " + pred + " ) cmd== quit"
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
                sift_engine(layer+1, pred + "cmd== quit")
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
                        pred = file.read().replace('\n', " cmd== ")
                        pred += "cmd== quit"
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
        # Get the list of commands
        cmd_line=' '.join(sys.argv[1:])
        # print("CmdLine: \"" + cmd_line + "\"")
    sift_engine(0, cmd_line)

# ================================================================================
