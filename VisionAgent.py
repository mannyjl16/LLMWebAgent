# Adapted from OpenAI's Vision example
from openai import OpenAI
import base64

# Point to the local server
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

#path = input("Enter a local filepath to an image: ")

def PromptVision(path,website_name):

  # Read the image and encode it to base64:
  base64_image = ""
  try:
    image = open(path.replace("'", ""), "rb").read()
    base64_image = base64.b64encode(image).decode("utf-8")
  except Exception:
    print("Couldn't read the image. Make sure the path is correct and the file exists.")
    exit()

  completion = client.chat.completions.create(
    model="xtuner/llava-phi-3-mini-gguf",
    messages=[
      {
        "role": "system",
        "content": "This is a chat between a user and an assistant. The assistant is helping the user to describe a webpages layout by its image.",
      },
      {
        "role": "user",
        "content": [
          {"type": "text", "text": f'''This is an image of a website called "{website_name}".
           In detail describe the contents of this website including:
            the specific buttons list the name each button visible, forms, any user interface
            any popups, Any headers or titles, Any text on the page
          If applicable Title each section of the page with the titles, Header, Main Content Area, Sidebar, and Footer
          Output in english and be as concise as possible and include all features of the website
          '''},
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/jpeg;base64,{base64_image}"
            },
          },
        ],
      }
    ],
    max_tokens=500,
    temperature=0,
    presence_penalty= 1.5,
    stream=False,
    stop="<|end|>"
  )
  return completion.choices[0].message.content
