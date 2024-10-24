#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import io
from IPython.display import Image, display, HTML
from PIL import Image
import base64
from dotenv import load_dotenv, find_dotenv
import requests, json


# In[2]:


# Read local .env file
_ = load_dotenv(find_dotenv()) 
hf_api_key = os.environ['HF_API_KEY']


# In[3]:


def get_completion(inputs, parameters=None, ENDPOINT_URL=""):
    headers = {
      "Authorization": f"Bearer {hf_api_key}",
      "Content-Type": "application/json"
    }   
    data = { "inputs": inputs }
    if parameters is not None:
        data.update({"parameters": parameters})
    response = requests.request("POST",
                                ENDPOINT_URL,
                                headers=headers,
                                data=json.dumps(data))
    return json.loads(response.content.decode("utf-8"))


# In[4]:


def get_completion(inputs, parameters=None, ENDPOINT_URL="", response_type="json"):
    headers = {
        "Authorization": f"Bearer {hf_api_key}",
        "Content-Type": "application/json"
    }
    data = {"inputs": inputs}
    if parameters is not None:
        data.update({"parameters": parameters})

    try:
        response = requests.post(ENDPOINT_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise an error for bad responses

        # Handle the response based on its type
        if response_type == "binary":
            return response.content  # Binary data, for image generation
        else:
            return json.loads(response.content.decode("utf-8"))  # JSON response, for captioning

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {"error": str(e)} if response_type == "json" else None


# In[5]:


ITT_ENDPOINT = os.environ['HF_API_ITT_BASE']
TTI_ENDPOINT = os.environ['HF_API_TTI_BASE']


# In[6]:


def image_to_base64_str(pil_image):
    byte_arr = io.BytesIO()
    pil_image.save(byte_arr, format='PNG')
    byte_arr = byte_arr.getvalue()
    return str(base64.b64encode(byte_arr).decode('utf-8'))

def base64_to_pil(img_base64):
    base64_decoded = base64.b64decode(img_base64)
    byte_stream = io.BytesIO(base64_decoded)
    pil_image = Image.open(byte_stream)
    return pil_image

def captioner(image):
    base64_image = image_to_base64_str(image)
    result = get_completion(base64_image, None, ITT_ENDPOINT, response_type="json")
    
    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"
    
    return result[0]['generated_text']

def generate(prompt):
    output = get_completion(prompt, None, TTI_ENDPOINT, response_type="binary")
    
    if output is None:
        return "Error: Unable to generate image."

    try:
        byte_stream = io.BytesIO(output)
        result_image = Image.open(byte_stream)
        return result_image
    except Exception as e:
        return f"Error: {e}"


# In[7]:


# Build your game with just captioning
import gradio as gr 

with gr.Blocks() as demo:
    gr.Markdown("# Describe-and-Generate Game")
    image_upload = gr.Image(label=
            "Your first image",type="pil")
    btn_caption = gr.Button("Generate caption")
    caption = gr.Textbox(label="Generated caption")
    
    btn_caption.click(fn=captioner, 
          inputs=[image_upload], outputs=[caption])

gr.close_all()
# demo.launch(share=True)
demo.launch()


# In[8]:


# Add generation
with gr.Blocks() as demo:
    gr.Markdown("# Describe-and-Generate Game")
    image_upload = gr.Image(label=
          "Your first image",type="pil")
    btn_caption = gr.Button("Generate caption")
    caption = gr.Textbox(label="Generated caption")
    btn_image = gr.Button("Generate image")
    image_output = gr.Image(label="Generated Image")
    btn_caption.click(fn=captioner, 
          inputs=[image_upload], outputs=[caption])
    btn_image.click(fn=generate, 
          inputs=[caption], outputs=[image_output])

gr.close_all()
# demo.launch(share=True)
demo.launch()


# In[9]:


# Add audio output
from gtts import gTTS

# Function to convert text to speech
def text_to_speech(text):
    tts = gTTS(text)
    tts.save("caption_audio.mp3")
    return "caption_audio.mp3"


# In[24]:


# Caption, audio and generation all at once
def caption_and_generate(image):
    caption = captioner(image)
    audio_file = text_to_speech(caption)
    image = generate(caption)
    return [caption, audio_file, image]

with gr.Blocks(css=".caption-audio-row { height: 100px; }") as demo:
    gr.Markdown("# Describe-and-Generate Game 💡")
    
    image_upload = gr.Image(label="Your first image", type="pil")
    btn_all = gr.Button("Caption and generate")

    with gr.Row():
        caption = gr.Textbox(label="Generated caption", lines=2.22)
        audio_output = gr.Audio(label="Caption Audio Output")
    
    image_output = gr.Image(label="Generated Image")

    btn_all.click(fn=caption_and_generate, 
                  inputs=[image_upload], 
                  outputs=[caption, audio_output, image_output])


gr.close_all()
# demo.launch(share=True)
demo.launch()


# In[11]:


gr.close_all()

