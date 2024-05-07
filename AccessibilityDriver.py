from playwright.sync_api import sync_playwright
from playwright._impl._cdp_session import CDPSession
import AccessibilityTree
import json
import LLMAgent
import re
import time
import VisionAgent
import Settings




class AgentBrowser:
    browser = None
    page = None
    client = None
    accessibility_tree = None
    current_url = "https://example.com"
    last_result = "(Start of task): No command has been executed yet"
    last_instruction = "No last instruction task has begun"
    website_name = "UNKNOWN SITE"
    original_prompt = ""
    reasoning_history = []
    #Functions
    def OutputPage(self,index=0):

        return self.website_name + self.accessibility_tree.get_output()[:16000]
    def Focus(self,id):
        self.client.send('DOM.focus', {'backendNodeId': int(id)})

    def LoadPage(self):
        self.client = self.page.context.new_cdp_session(self.page)
        self.client.send("Accessibility.enable")
        snapshot = self.page.accessibility.snapshot()
        self.accessibility_tree = AccessibilityTree.AccessibilityTree(self.client, snapshot)
        self.current_url = self.page.url
        rootAxNode = self.client.send('Accessibility.getRootAXNode')
        self.website_name = "Website: " + rootAxNode["node"]["name"]["value"] + '\n'
    def Navigate(self,url="https://example.com"):

        to_url = url.replace('"','').replace("'",'')
        self.page.goto(to_url)
        self.LoadPage()
        return "Navigated to " + to_url
    def Expand(self,params):
        return self.accessibility_tree.expand_node(params[0])
    def Scroll(self):
        self.accessibility_tree.chunk_index += 1

        current_line =  self.accessibility_tree.chunk_index * self.accessibility_tree.chunk_length
        scroll_to =  int(min([len(self.accessibility_tree.full_tree)-1,(self.accessibility_tree.chunk_index * self.accessibility_tree.chunk_length)]))# scroll half way
        if len(self.accessibility_tree.full_tree) > scroll_to:

            self.page.mouse.wheel(0, 250)
            #if scroll_to < current_line:
             #   self.page.keyboard.down('End')
            scroll_node = self.accessibility_tree.full_tree[scroll_to]
            scroll_id = scroll_node["backendDOMNodeId"]
            self.client.send('DOM.scrollIntoViewIfNeeded', {'backendNodeId': int(scroll_id)})
            time.sleep(2)  # Allow scrolled elements to load
            return "Scrolled down"
        else:
            self.accessibility_tree.chunk_index = 0
            return "Exception: Failed to scroll end of page reached"
    def Click(self,params):
        node_id = params[0]

        current_node = self.accessibility_tree.getNodeByDomId(node_id)
        self.Focus(node_id)
        focused_element = self.page.evaluate_handle('document.activeElement')
        focused_element.click();
        return "Clicked " + current_node["name"]["value"]
    def Read(self,params):
        node_id = params[0]

        current_node = self.accessibility_tree.getNodeByDomId(node_id)
        self.Focus(node_id)
        focused_element = self.page.evaluate_handle('document.activeElement')
        return "Text Read: " + focused_element.text_content()
    def Enter(self):
        focused_element = self.page.evaluate_handle('document.activeElement')
        focused_element.press('Enter')
        return "Pressed Enter"
    def input_command(self,params):
        node_id = params[0]

        current_node = self.accessibility_tree.getNodeByDomId(node_id)


        self.Focus(node_id)
        focused_element = self.page.evaluate_handle('document.activeElement')

        focused_element.type(params[1])
        return "Inputted the text " + params[1] + " to " + current_node["name"]["value"]





        '''
               List of LLM functions:
               [X]Navigate(link) - navigates to a webpage and then gets the content
               [X]Scroll() - Scrolls down a single chunk so the display will display next chunk
               [x]Click(index) - clicks an element at index
               [x]Input(index,string) - inputs desired text into a combobox,textarea,input etc
               [Deprecated]Expand(index) - sets the node at index to expanded the children of the indexed node will now be visible
               [Not implemented]Find(str) - uses a similarity search to look through ALL of the nodes in the body and returns a list of closest matching nodes(USE SORTING)
               [Deprecated]Read(index) - Reads the text attribute at the index and passes it into the prompt
               [X]Loop() - restarts the instruction loop
               [Not implemented]Wait()
               [Not implemented]PromptFeedBack('Question') - Ask the user for feedback on what to do next

               [x]EndTask() - Finishes the task and starts the llm over

               '''
    #Find the desired command and extract the parameters for a function call
    def ExecuteCommand(self,command):
        pattern = r"(?<=\().+?(?=\))"
        match = re.search(pattern, command)
        params = []
        if match:
            extracted_string = match.group()
            params = extracted_string.split(",")
        try:
            if command.find('Input') != -1 and len(params) > 1:

                return self.input_command(params)
            elif command.find('Navigate') != -1 and len(params) > 0:
                return self.Navigate(params[0])
            elif command.find('Click') != -1 and len(params) > 0:
                return self.Click(params)
            elif command.find('EndTask') != -1:
                return "Task End - summarize what you did"
            elif command.find('Scroll') != -1:
                return self.Scroll()
            elif command.find('Expand') != -1 and len(params) > 0:
                return self.Expand(params)
            elif command.find('Read') != -1 and len(params) > 0:
                return self.Read(params)
            elif command.find('Enter') != -1:
                return self.Enter()
            else:
                return "Exception: Unknown Command"
        except Exception as e:
            print(e)
            return "Exception failed to execute: " + command

    #Main agent loop(Planner and command creator communication)
    def AgentLoop(self):
        while True:
            starting_page = "https://example.com"
            if Settings.Initial_Page is not None:
                starting_page = Settings.Initial_Page
            self.Navigate(starting_page)
            prompt = input("Prompt AI to complete task:\n")
            self.original_prompt = prompt
            if Settings.UsePlanner:
                prompt = LLMAgent.create_planner(prompt)
            attempts = 0
            print(prompt)
            while True:
                self.reasoning_history.clear()
                if attempts > Settings.Max_Attempts:
                    break
                instruction_list = prompt[prompt.lower().find("instructions:") + 13:].split('\n')
                #for i in range(len(instruction_list)):
                i = 0
                while i < len(instruction_list): #Cheesy for loop so i can change iterator
                    instruction = instruction_list[i]
                    if len(instruction) < 3:
                        i += 1
                        continue
                    if instruction.lower().find("loop") == 0:
                        i = 0
                        continue
                    print("\nStep: " + str(i))
                    print(instruction)
                    tree_view = self.OutputPage()
                    if Settings.ShowTree:
                        print(tree_view)
                    com_prompt = tree_view + "\n\n Instruction:\n" + instruction
                    command_plan = LLMAgent.create_commands(com_prompt, self.website_name)
                    print("\nCommand Agent:\n" + command_plan)
                    command = command_plan[command_plan.lower().find("command:") + 8:]

                    self.reasoning_history.append("Reasoning Step " + str(i) + ':\n' + instruction + '\n' + command_plan)
                    if len(self.reasoning_history) > 15: # Prevent the reasoning history from getting to big
                        del self.reasoning_history[0]
                    if command.lower().find("exception") != -1: #Command maker decided it could not find the node
                        print("Could not find NODE!")
                        self.last_result = command
                        break
                    self.last_result = self.ExecuteCommand(command)
                    if self.last_result.lower().find("exception") == 0:
                        print("Failed to execute command!")
                        break
                    self.last_instruction = instruction
                    time.sleep(1)  # Wait a bit for page to fully load
                    # Update the new accessibility tree
                    self.accessibility_tree.update_tree(self.page)
                    self.current_url = self.page.url
                    rootAxNode = self.client.send('Accessibility.getRootAXNode')
                    self.website_name = "Website: " + rootAxNode["node"]["name"]["value"] + '\n'
                    i += 1
                if Settings.UseUpdater and self.last_result.lower().find("exception") == 0:
                    #Add code to update planner with screenshot of page
                    self.page.screenshot(path='screenshot.png', type="png")
                    page_summary = VisionAgent.PromptVision("screenshot.png",self.website_name)
                    print("Summary of page: " + page_summary)
                    prompt = LLMAgent.update_plan(prompt, self.original_prompt, self.website_name, self.reasoning_history, page_summary)
                    print("Update Plan Agent:\n" + prompt)
                    attempts += 1
                    continue

                input("Task completed! press any key to do another:")
                break

    def __init__(self):
        with sync_playwright() as p:
            self.browser = p.chromium.launch(channel="chrome", headless=Settings.Headless)
            self.page = self.browser.new_page()
            self.AgentLoop()

    def __exit__(self, *args):
        self.browser.close()






