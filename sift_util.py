# ================================================================================
# sift_util.py
# Utility functions, etc. for the Test machine for
# the Rules Engine for the Game of Sifteyond
#
# Author:  Paul Melville
# Created: 25 APR 2023
# ================================================================================
import inspect

# ================================================================================
def currFunc(): 
    frame = inspect.currentframe()
    return inspect.getouterframes(inspect.currentframe())[1].function

# ================================================================================
def match_cmd(text, key):
    keylen = len(key)
    if keylen == 0:
        return False
    if len(text) < keylen:
        return False
    if text[:keylen] != key:
        return False
    return True

# ================================================================================
def grab_predic8(text, key, delim=" "):
    fullkey = key + delim
    if not match_cmd(text, fullkey):
        return ""
    return text[len(fullkey):]

# ================================================================================
# Given a File, read it into a (possibly quite long) Text String
# Fish out the Value of the Key
# ================================================================================
def file_text(filename):
    try:
        fyle = open(filename, 'r')
    except IOError:
        print("Cannot open file \"" + filename + "\" for Reading")
        return None

    text = fyle.read().replace("\n", " ")
    fyle.close()
    return text

# ================================================================================
# Given a (possibly quite long) Text String, Search it for a Key
# Then, if found, assuming some syntactical elements (as per JSON)
# Fish out the Value of the Key
# ================================================================================
def file_search_delim(text, delim):
    val = ""
    #print("Searching in <{}>".format(text[:20]))
    pos = text.find(delim)
    if pos >= 0:
        valtext = text[pos+1:]
        #print("FoundSomething here <{}>".format(valtext[:20]))
        rdelim = delim
        if delim == "[":
            rdelim = "]"
        if delim == "(":
            rdelim = ")"
        if delim == "{":
            rdelim = "}"
        if delim == "<":
            rdelim = ">"
        pos = valtext.find(rdelim)
        if pos > 0:
            val = valtext[:pos]
            #print("FoundCompletion thus <{}>".format(val))
            text = valtext[pos+1:]
    return text,val

# ================================================================================
# Given a (possibly quite long) Text String, Search it for a Key
# Then, if found, assuming some syntactical elements (as per JSON)
# Fish out the Value of the Key
# ================================================================================
def file_search(text, key):
    pos = text.find(key)
    if pos >= 0:
        text = text[pos:]
    return text,pos
    
# ================================================================================
# Given a (possibly quite long) Text String, Search it for a Key
# Then, if found, assuming some syntactical elements (as per JSON)
# Fish out the Value of the Key
# ================================================================================
def file_search_val(text, key):
    val = ""
    newtext,pos = file_search(text, key)
    if pos == -1:
        # Key Not Found
        return text,val
    # zip forward to after the key & some whitespace
    newtext = newtext[len(key)+2:]
    endtext,valpos = file_search(newtext, ",")
    if valpos == -1:
        endtext,valpos = file_search(newtext, "}")
    if valpos == -1:
        # Giving Up!
        print("\tNo End Val Delimeter for Key \"" + key + "\"")
        return text,val

    # TBD pluck out the Value
    val = newtext[:valpos].strip(']').strip().strip('}').strip().lstrip().strip('"').lstrip('"')
    endtext = endtext[1:]
    return endtext,val

# ================================================================================

# ================================================================================

# ================================================================================

# ================================================================================
