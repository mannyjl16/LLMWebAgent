from typing import Final

from groq import Groq
from dotenv import load_dotenv
import os


load_dotenv()
GROQKEY: Final[str] = os.getenv('GROQ_APIKEY')
groq_client = Groq(api_key=GROQKEY)


def prompt_groq(prompts,sysprompt="You are an AI assistant",modelName="llama3-8b-8192"):
    """
    Prompt the Groq chatbot with a list of prompts and return the response.

    Args:
        prompts (list): List of prompts to send to the chatbot.
        sysprompt (str): System prompt to start the conversation.
        modelName (str): Name of the model to use for the chatbot.

    Returns:
        str: The response from the chatbot.

    Raises:
        None
    """
    msgs = [{"role": "system", "content": sysprompt}]

    msgs.extend(iter(prompts))
    completion = groq_client.chat.completions.create(
        model=modelName,
        messages=msgs,
        temperature=0,
        max_tokens=1200,
        stream=False
    )
    return completion.choices[0].message.content


def create_planner(prompt):
    """
    Create a planner for generating a list of instructions to carry out a given task and interact with a web browser.

    Args:
        prompt (str): The prompt to start the planner process.

    Returns:
        str: The response from the chatbot after generating the planner instructions.

    Raises:
        None
    """
    PlannerPrompt = '''You are a self operating web browser.
    Your task is to think through and then create a list of instructions to carry out the given task.
    Your instructions will be passed to a human.
    The human will be able to Click on links and buttons based on their name, Navigate to a new webpage based on url, Input to forms, Scroll down on the page, Press enter, and Loop back to the first instruction.
    After sending an input command you will need to send an enter command to press enter. Unless the task specifies a click after
    If no text is specified to input, improvise the text to input based on the context
    If you need to go to a website and no link is specified, choose a link.
    Start by creating a thought with the title Thought:
    In this thought think through how to complete the task step by step. Use the most efficient way of completing the task
   
    Then for the instruction list give it the exact title Instructions:
    Then list the steps to complete the task.
    Each instruction in the list should be separated by a newline.
    Each instruction should be verbose and contain details about what is being interacted
    I.e if the task is to click the first video on youtube dont just say Click the first link.
    Say Click the first link that leads to a video.
    Do not put anything that is not an instruction under the Instructions: title, whether it may be comments or summaries.
    this is because everything after "Instructions:" Needs to be executed sequentially line by line
    Use the minimal amount of instructions needed. Assume you are only creating one plan. Do not use any instructions that the next agent cannot perform
    
    Example:
    Goto youtube click the first video on youtube and write a nice comment
    
    Thought: Ok so to complete this task I will start by navigating to https://youtube.com.
    Then I will need to click on the first video. After that I will need to scroll down to the comment section.
    Then I should input "Hi I really liked this video!" into the comment box
    
    Instructions:
    Navigate to https://youtube.com
    Click the first video
    Scroll down
    Input Hi I really liked this video! into the comment box
    
    This example shows the proper format your output should be
'''
    prompts = [{"role": "user", "content": prompt}]
    return prompt_groq(prompts, PlannerPrompt,modelName="llama3-70b-8192")
def update_plan(plan,original_prompt,webname="default",reasoning_steps=None,page_summary="No website shown"):
    """
    Update a planner by revising a list of instructions based on the last plan, current webpage layout, reasoning steps, and original task.

    Args:
        plan (str): The original plan to be updated.
        original_prompt (str): The original prompt for the task.
        webname (str): Name of the website being interacted with (default is "default").
        reasoning_steps (list): List of reasoning steps to consider for the update.
        page_summary (str): Summary of the current webpage layout (default is "No website shown").

    Returns:
        str: The response from the chatbot after updating the planner instructions.

    Raises:
        None
    """

    update_prompt = f'''You are a self operating web browser.
    Your task is to revise a list of intructions to complete based on the last plan, the current webpage layout, the reasoning steps before and the Original Task.
    Your instructions will be passed to a human.
    The human will be able to Click on links and buttons based on their name, Navigate to a new webpage based on url, Input to forms, Scroll down on the page, Press enter, and Loop back to the first instruction.
    After sending an input command you will need to send an enter command to press enter. Unless the task specifies a click after
    If no text is specified to input, improvise the text to input based on the context
    If you need to go to a website and no link is specified, choose a link.
    
    Start by creating a thought with the title Thought:
    In this thought think through how to complete the task step by step.
    Incorporate information about the current webpage layout to understand where the instructions might have gone wrong.
    Also utilize information about the previous reasoning steps.
    Use the names of specific features of the page to understand why the task failed
    Use the most efficient way of completing the task
    
    
    Then for the instruction list give it the exact title Instructions:
    Then list the steps to complete the task.
    Each instruction in the list should be separated by a newline.
    Each instruction should be verbose and contain details about what is being interacted
    I.e if the task is to click the first video on youtube dont just say Click the first link
    Say Click the first link that leads to a video
    Do not put anything that is not an instruction under the Instructions: title, whether it may be comments or summaries.
    this is because everything after "Instructions:" Needs to be executed sequentially line by line
    Use the minimal amount of instructions needed. Assume you are only creating one plan. Do not use any instructions that the next agent cannot perform
    
    Website Name:
    {webname}
    
    Webpage layout:
    {page_summary}
    
    Original Task:
    {original_prompt}
    
    '''
    prompts = [
        {"role": "user", "content": reason_step}
        for reason_step in reasoning_steps
    ]
    prompts.append({"role": "user", "content": plan})
    return prompt_groq(prompts, update_prompt,modelName="llama3-70b-8192")

def create_commands(prompt,webname):
    """
    Create commands based on a given prompt and website name to interact with elements in an accessibility tree.

    Args:
        prompt (str): The prompt to generate commands for.
        webname (str): Name of the website being interacted with.

    Returns:
        str: The response from the chatbot after generating the commands.

    Raises:
        None
    """
    return prompt_groq(
        [{"role": "user", "content": prompt}],
        f'''This is an accessibility tree, it has elements with their index, name and role.
        Your task is to form a thought about the instruction and create a single command based on the single intruction you were given
        if you want to click something output 'Click(index)' it takes one parameter the index of the element

        Command Example:
        88 button Login
        71 link Sign Up
        Instruction: Click the login button
        Thought:
        Ok so based on my two options link Sign up and button login. I would say that although similar, 88 button login is my best option to click 
        Command: Click(88)
        if you want to Input to a field type 'Input(index,'desired_text')' it takes two parameters the index of the element and the text to send
        Do not put the desired text in quotes unless explicitly specified to

        Command Example:
        22 combobox Fin stuff
        875 link More options
        Instruction:
        Input Burger into the search bar
        Thought:
        Ok so based on the accessibility tree I can see that theres two options being combobox Find Stuff and link More options
        Since 22 combobox Find Stuff is an element I can input text into. 
        And its name implies a similar meaning I will assume this is the closest match to input Burger into
        Command:
        Input(22,Burger)

        if you are asked to scroll down type 'Scroll()' Also do this if you dont see the node being referred to
        If you are asked to press enter type 'Enter()'
        If you are asked to go to a website type 'Navigate(desired_url)' it takes one parameter which is the url

        Command Example:
        22 StaticText BestWorld
        55 button See more options
        Instruction:
        Navigate to https://google.com
        Thought:
        Since the instruction is to navigate to https://google.com I will do just that.
        Command: Navigate(https://google.com)

        if the instruction is to end the task output 'EndTask()'
        If you do not see anything that is related enough output 'Exception: Could not find the node'

        Command Example:
        22 StaticText BestWorld
        55 button See more options
        77 combobox Search
        Instruction:
        Input "Hot dogs" into the document
        Thought:
        Based on the accessibility tree I can see that there is nothing explicitly related to inputting into a document.
        Although there is a combobox called search. Its name implies it has an entirely different function to what the instruction intends.
        There for I will create an exception.
        Command:
        Exception: Could not find the node

        Start by creating a thought and give it the exact title Thought:
        If the instruction asks you to click or input to an element. Then work out which of the elements are most likely to correspond with the instruction based on their role and name
        Then determine the best possible option to incorporate into your output

        Next create a command and give it the exact title Command:
        Your command should only be a single command to execute with no commentary as concise as possible
        Current Site is: {webname}
        Write your thought and command to execute now
        ''',
    )
