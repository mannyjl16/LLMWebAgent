# LLMWebAgent
A simple open source LLM Web automator using a 4 agent pipeline.

**Getting Started:**
<br>
1. download the files into a project folder<br>
2. install google chrome<br>
3. install LMStudio and set up a local server with the "xtuner/llava-phi-3-mini-gguf" model for vision<br>
4. install the necessary python dependencies. Dotenv, Groq, OpenAI, Playwright, etc<br>
5. set your groq api key in the .env file<br>
6. Read(How to use)<br>
7. run main.py<br>
<br>

**How to use:**
<br>
After completeing the setup. You will be prompted to enter a task<br>
The task must utilize the controls available. Those are click, input, navigate to url, scroll down, enter and loop<br>
The planner will break down the tasks into instructions which the command executor can interpret.<br><br>
Example:<br>
Goto facebook. Search for Burgers. Scroll down and click the first link related to Burgers.<br>
<br>
You can watch your task be executed step by step by watching the browser.<br>
When the task is finished you can start another task<br>
To loop the task make sure to tell it to loop at the end of your instruction.<br>

Do not be too abstract with your requests. Start small and work your way up. It wont be able to do something like buy amazon products and write reviews.<br>
If you have a more complex task possibly ditch the planner all together in the settings and use the chrome accessibility tree to debug the names of elements and 
step by step plan out your entire task. Make sure to put a new line after each instruction if you do this.<br>


**How it works:** <br>
This implementation uses a simple 4 LLM agent pipeline. The agents being the planner, the command executor and the planner updater.
The planner takes an intial prompt and creates a thought about how to go about completing the task. Then creates a list of instructions for the executor to carry out
The executor sees a chrome accessibility tree of the current page. Including the ID, role and name of each element. The command executor then generates a thought 
and decides which function best suits the instruction given and to which node it applies if necessary.
The functions it can execute are Navigate(url), Click(ID), Input(ID,text), Enter(), Loop(), Sroll()
Example:
Goto google. Search for Cars. Scroll down and click the first link related to cars
<br><br>
Which the planner may compile to<br>
Navigate to google.com<br>
Input Cars into the search bar<br>
Press enter<br>
Scroll down<br>
Click the first search result related to cars<br>
<br>
and then it may get executed as:
Navigate(google.com)<br>
Input(72,Cars)<br>
Enter()<br>
Scroll()<br>
Click(5678)<br><br>
This loop will run for each instruction step until it ends or something happens
In case of an exception, a screenshot is taken of the current webpage. Then an LLM with vision describes the webpage.
The description of the webpage as well as the last plan, original prompt and all the previous commands executed is sent to the update planner. The planner determines where the execution went wrong and creates a new plan to execute.
<br>

**Optional** <br>
Modify the Settings.py to your liking<br>
Edit the system prompt in the LLMAgent.py<br>
Replace the vision model and agents with something like GPT4 or claude for better generalizations and task success<br>
Modify the pipeline<br>
