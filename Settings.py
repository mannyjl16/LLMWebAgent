#Whether or not the accessibility tree displays only focusable elements
OnlyFocusable = True

#Whether or not to use the full accessibility tree or just built in snapshot
UseFullTree = True

#The max characters the tree can output
Tree_Context_Cap = 16000

#The max length of each displayed Node
Max_Node_Size = 100

#Whether or not to use the planner and without this you need step by step instructions with a new line after each one
UsePlanner = True

#Whether or not an agent will attempt to correct the instruction list if the first one failed
UseUpdater = True

#Set to initial page url or None for example.com
Initial_Page = None #Default None

#The maximum number of attempts the bot has to perform the task
Max_Attempts = 5

#Whether or not to show the web tree
ShowTree = False

#Whether or not to run the browser in headless mode(Only use after testing throughly)
Headless = False