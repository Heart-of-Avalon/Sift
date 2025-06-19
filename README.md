================================================================================
# Sift
================================================================================
SIFT - Scripted Interactive Functional Test
================================================================================

The Basic Flow of the Test Utility
================================================================================
The Python implementation of the "Scripted Interactive Functional Test" (SIFT)
engine is in (sift_engine.py) which uses (sift_util.py)

To invoke commands for the test-target, use the "bash" command from sift

Start in Main
================================================================================
python3 sift_engine [ cmds ]

Will execute "cmds" accroding to the Lexical parsing engine,
then continue interactively by awaiting user input at a prompt.
<cmds> can follow the format: <cmd0> cmd==<cmd1> cmd==<cmd2> ...
in order to execute a number of commands serially.

something like:   echo Hello cmd==quit
will execute the commands and conclude with "quit"

================================================================================
VARIABLE SUBSTITUTION
================================================================================
For any input line (from a script or from interactive command line),
Any sequence such as $<variable-name> is replaced with <variable-value>
based on the variable-name having been defined, using a command like this:

    var <variable-name>=<variable-value>

So, consider this mini-script:
    var namae=Larry
    echo $namae
OUTPUT: Larry

================================================================================
Commands:
SIFT:
<blank line>
	(Do Nothing)

# ANY-TEXT
	ANY-TEXT is a Comment (Do Nothing)

nop
	Do Nothing

quit  OR  exit
	Terminate the current layer of interaction

bash <command> <parameters>
	Execute "<command> <parameters>" as a sub-process in a bash shell

dos <command> <parameters>
	Execute "<command> <parameters>" as a sub-process in a DOS shell

py <parameters>
	Execute "python3 <parameters>" as a sub-process in a bash/DOS shell
	Example:
		py fun.py
		Execute "python3 fun.py" as a sub-process in a bash shell

hunt <search-string> <filename>
	Use a bash sub-process to search (grep) for <search-string> in <filename>

sleep <N>
	Pause, Idle for <N> miliseconds

echo ANY-TEXT
	Write ANY-TEXT to console output

file <file-name> [ clear | write | read ] <text>
	Clear <file-name>, Read <file-name>, or Write (append!) <text> to the end of <file-name>

prompt <prompt-text>
	Show <prompt-text> and interactively accept user input.
	User response is found in $response

var <varname>=<value>
	Set global symbol <varname> to map to <value>
	NOTE: if <value> == "XXX", then remove global symbol <varname> from the list
var <varname>=eval( expr )
	ALTERNATE: as a special case, Evaluate expr as a python expression, then do:
		var <varname>=<expr-value>
	NOTE: Can use Variable Substitution in any command, comment, etc:
	  Replace $varname , ${varname} ,  or $(varname) with <value>

module <module-name>=<module-cmd>
	Set global module <module-name> to map to <module-cmd>
	NOTE: if <module-cmd> == "XXX", then remove global module <module-name> from the list
	NOTE: Can use <module-name> as a command, like this
	      <module-name> <parameters>
		Execute "<module-cmd> <parameters>" as a sub-process in a bash/DOS shell
	Example:
		module hwc sendhwc
		hwc Beep
		--> runs shell sub-process: "sendhwc Beep"

push <value>
	Push <value> onto the Variable Stack

pop <varname>
	Pop the Variable Stack, doing var varname=<popped-value>

jump <label>
	Search current script for a line with "LABEL <label>"
	   and resume script processing from there
	      by updating Current Script Location (CSL)
	   NOTE: Typically in a Comment:  # LABEL start_loop

call <label>
	Search current script for a line with "LABEL <label>"
	   then, push CSL and R0-R7 onto the Variable Stack
	   then, resume script processing from LABEL <label>

return [ <value> ]
	var ret=<value>
	then pop R0-R7 and CSL from the Variable Stack
	then, resume script processing from the new CSL

eval( expr )
      	Evaluate expr as a python expression
	var result=<expr-value>
	Examples:
		eval( 2 + 5 )				var result=7
		eval( "${response}" == "resign" )	var result=False
		eval( "A1" in "${NodeList}" )		var result=True
	NOTE: This command has been intentionally hobbled to prevent
	      execution of "dangerous code"

if( expr ) <cmd>
    	Evaluate expr as a python expression
	then, if the $result is not False and not Zero
	execute <cmd> as an additional command
	Examples:
		if( $turn + 2 < $max )      echo Too Many Turns
		if( $nodeCount > 1 )        call fixNodeCount
		if( $nodeCount < $maxNode ) jump loop_start

layer <cmds>
        start a new processing layer and execute <cmds> in it
	NOTE: "quit" will exit the layer
	      and resume processing in the original layer

script <scriptname>  OR   <scriptname>
        find a file named <scriptname> open it and then
        start a new processing layer to
	process each line as a new command
	NOTE: "quit" will exit the layer/script
	      and resume processing in the original layer
