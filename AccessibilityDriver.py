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
    """
    AgentBrowser class for controlling a browser agent to interact with elements in an accessibility tree.

    Functions:
    - OutputPage(index=0): Get the output of the website's accessibility tree.
    - Focus(id): Focus on a specific element by its ID.
    - LoadPage(): Load the page and initialize the accessibility tree.
    - Navigate(url="https://example.com"): Navigate to a specified URL.
    - Expand(params): Expand a node in the accessibility tree.
    - Scroll(): Scroll down the page.
    - Click(params): Click on a specific element.
    - Read(params): Read text content of a specific element.
    - Enter(): Simulate pressing the Enter key.
    - input_command(params): Input text into a specific element.
    - ExecuteCommand(command): Execute the given command.
    - AgentLoop(): Main loop for planner and command creation communication.
    """
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

    def __init__(self):
        with sync_playwright() as p:
            self.browser = p.chromium.launch(channel="chrome", headless=Settings.Headless)
            self.page = self.browser.new_page()
            self.AgentLoop()

    def __exit__(self, *args):
        self.browser.close()

    #Functions
    def OutputPage(self,index=0):
        """
        Return the output of the website's accessibility tree up to a specified character limit.

        Args:
            index (int): Index parameter for the output (default is 0).

        Returns:
            str: The concatenated website name and the truncated output of the accessibility tree.
        """
        return self.website_name + self.accessibility_tree.get_output()[:Settings.Tree_Context_Cap]
    
    def Focus(self,id):
        """
        Focus on a specific element by sending a DOM focus command with the backend node ID.

        Load the page and initialize the client for interacting with the page context.
        """
        self.client.send('DOM.focus', {'backendNodeId': int(id)})

    def LoadPage(self):
        """
        Initialize the client for interacting with the page context, enable accessibility, and create the accessibility tree.

        Updates the current URL and sets the website name based on the root AX node.

        Args:
            None

        Returns:
            None
        """
        self.client = self.page.context.new_cdp_session(self.page)
        self.client.send("Accessibility.enable")
        snapshot = self.page.accessibility.snapshot()
        self.accessibility_tree = AccessibilityTree.AccessibilityTree(self.client, snapshot)
        self.current_url = self.page.url
        rootAxNode = self.client.send('Accessibility.getRootAXNode')
        self.website_name = "Website: " + rootAxNode["node"]["name"]["value"] + '\n'

    def Navigate(self,url="https://example.com"):
        """
        Navigate to a specified URL, load the page, and update the accessibility tree.

        Args:
            url (str): The URL to navigate to (default is "https://example.com").

        Returns:
            str: A message indicating the navigation to the specified URL.
        """
        to_url = url.replace('"','').replace("'",'')
        self.page.goto(to_url)
        self.LoadPage()
        return f"Navigated to {to_url}"
    
    def Expand(self,params):
        """
        Expand a node in the accessibility tree based on the provided parameters.

        Args:
            params (list): List containing the parameters for expanding the node.

        Returns:
            str: The result of expanding the specified node.
        """
        return self.accessibility_tree.expand_node(params[0])
    
    def Scroll(self):
        """
        Increment the chunk index for scrolling, scroll down the page, and handle reaching the end of the page.

        Returns:
            str: The result of the scroll operation or an exception message if the end of the page is reached.
        """
        self.accessibility_tree.chunk_index += 1

        scroll_to =  int(min([len(self.accessibility_tree.full_tree)-1,(self.accessibility_tree.chunk_index * self.accessibility_tree.chunk_length)]))# scroll half way
        if len(self.accessib.ility_tree.full_tree) > scroll_to:
            return self._extracted_from_Scroll_8(scroll_to)
        self.accessibility_tree.chunk_index = 0
        return "Exception: Failed to scroll end of page reached"

    # TODO Rename this here and in `Scroll`
    def _extracted_from_Scroll_8(self, scroll_to):
        """
        Perform the scroll operation by simulating mouse wheel movement and scrolling to a specific node in the accessibility tree.

        Args:
            scroll_to (int): Index of the node to scroll to.

        Returns:
            str: A message indicating that the scroll operation was successful.
        """
        self.page.mouse.wheel(0, 250)
        scroll_node = self.accessibility_tree.full_tree[scroll_to]
        scroll_id = scroll_node["backendDOMNodeId"]
        self.client.send('DOM.scrollIntoViewIfNeeded', {'backendNodeId': int(scroll_id)})
        time.sleep(2)  # Allow scrolled elements to load
        return "Scrolled down"
    
    def Click(self,params):
        """
        Click on a specific element identified by the node ID in the accessibility tree.

        Args:
            params (list): List containing the node ID of the element to click.

        Returns:
            str: A message indicating that the element was clicked.
        """
        node_id = params[0]

        current_node = self.accessibility_tree.getNodeByDomId(node_id)
        self.Focus(node_id)
        focused_element = self.page.evaluate_handle('document.activeElement')
        focused_element.click();
        return "Clicked " + current_node["name"]["value"]
    
    def Read(self,params):
        """
        Read the text content of a specific element identified by the node ID in the accessibility tree.

        Args:
            params (list): List containing the node ID of the element to read.

        Returns:
            str: The text content read from the element.
        """
        node_id = params[0]

        self.Focus(node_id)
        focused_element = self.page.evaluate_handle('document.activeElement')
        return f"Text Read: {focused_element.text_content()}"
    
    def Enter(self):
        """
        Presses the Enter key on the currently focused element.

        Returns:
            str: A message indicating that Enter key was pressed.
        """
        focused_element = self.page.evaluate_handle('document.activeElement')
        focused_element.press('Enter')
        return "Pressed Enter"
    
    def input_command(self,params):
        """
        Inputs text into the specified node element.

        Args:
            params (list): A list containing the node ID and text to input.

        Returns:
            str: A message indicating the text that was inputted.
        """
        node_id = params[0]

        current_node = self.accessibility_tree.getNodeByDomId(node_id)


        self.Focus(node_id)
        focused_element = self.page.evaluate_handle('document.activeElement')

        focused_element.type(params[1])
        return f"Inputted the text {params[1]} to " + current_node["name"]["value"]
    
    #Find the desired command and extract the parameters for a function call
    def ExecuteCommand(self,command):
        """
        Executes the specified command by parsing it and calling the corresponding method.

        Args:
            command (str): The command to be executed.

        Returns:
            str: The result or message after executing the command.
        """
        pattern = r"(?<=\().+?(?=\))"
        match = re.search(pattern, command)
        params = []
        if match:
            extracted_string = match.group()
            params = extracted_string.split(",")
        try:
            # TODO: use case/match instead
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
            return f"Exception failed to execute: {command}"

    #Main agent loop(Planner and command creator communication)
    def AgentLoop(self):
        """
        Executes a loop for the AI agent to interact with a web page based on given instructions and commands.
        """
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

                    self.reasoning_history.append(
                        f"Reasoning Step {i}"
                        + ':\n'
                        + instruction
                        + '\n'
                        + command_plan
                    )
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
                    self.page.screenshot(path='screenshot.png')
                    page_summary = VisionAgent.PromptVision("screenshot.png",self.website_name)
                    print(f"Summary of page: {page_summary}")
                    prompt = LLMAgent.update_plan(prompt, self.original_prompt, self.website_name, self.reasoning_history, page_summary)
                    print("Update Plan Agent:\n" + prompt)
                    attempts += 1
                    continue

                input("Task completed! press any key to do another:")
                break
