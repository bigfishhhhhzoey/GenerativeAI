# Describe-and-Generate Game with Gradio

## Overview
This project is an interactive **Describe-and-Generate Game** built using Gradio, Hugging Face APIs, and Python. The game allows users to upload an image, generate a caption for the image, convert the caption to an audio output, and even generate a new image based on the caption.

## Features
1. **Image Captioning**: Upload an image and generate a text caption describing the image using the `Salesforce/blip-image-captioning-large` model for image-to-text (ITT).
2. **Audio Output**: Convert the generated caption into audio using Google Text-to-Speech (gTTS).
3. **Image Generation**: Use the generated caption to create a new image using the `stabilityai/stable-diffusion-3.5-large` model.
4. **Interactive Interface**: An easy-to-use interface built using Gradio Blocks.
1. **Image Captioning**: Upload an image and generate a text caption describing the image using Hugging Face's image-to-text model.
2. **Audio Output**: Convert the generated caption into audio using Google Text-to-Speech (gTTS).
3. **Image Generation**: Use the generated caption to create a new image.
4. **Interactive Interface**: An easy-to-use interface built using Gradio Blocks.

## Technologies Used
- **Models Used**: 
  - **Image Captioning**: `Salesforce/blip-image-captioning-large` (ITT)
  - **Image Generation**: `stabilityai/stable-diffusion-3.5-large` (TTI)
- **Gradio**: For building the interactive UI.
- **Hugging Face APIs**: For image-to-text (ITT) and text-to-image (TTI) functionalities.
- **gTTS**: To convert generated text captions to audio.
- **Python**: The main language for building the game.

## Setup

### Prerequisites

- Python 3.x
- Hugging Face API access token
- Gradio for the user interface
- PIL for image processing
- IPython for displaying images

### Install the Required Libraries

Install the necessary Python libraries with:

```bash
pip install gradio gtts requests pillow python-dotenv
```

### Hugging Face API Key

You will need to set up your Hugging Face API key to access the models. Create a `.env` file in the root directory with the following content:

```
HF_API_KEY=your_hugging_face_api_key
HF_API_TTI_BASE=https://api-inference.huggingface.co/models/your-tti-model
HF_API_ITT_BASE=https://api-inference.huggingface.co/models/your-itt-model
```

Make sure to replace `your_hugging_face_api_key` and model URLs with your actual Hugging Face key and model endpoint URLs.

### Run the App

After setting up the environment variables and installing the necessary packages, run the Python script to start the Gradio app:

```bash
python image_process.py
```

The app will launch in your web browser, and you can start uploading images and generating captions and new images.

## Usage
- **Upload an Image**: Upload your first image to the Gradio interface.
- **Generate Caption**: Click on the "Generate Caption" button to see a description of your uploaded image.
- **Audio Output**: Convert the generated caption to audio by using the audio output block.
- **Generate Image**: Create a new image based on the generated caption.

## Project Walkthrough
- **Basic Game**: Initially, users can upload an image and generate a caption using the ITT model.
- **Image Generation**: Added functionality to create a new image based on the generated caption using TTI.
- **Caption Audio Output**: Finally, added a feature to convert the generated caption to speech for better engagement.

## Reference
This project follows the lessons from the **[Hugging Face and Gradio Course - Describe and Generate Game](https://learn.deeplearning.ai/courses/huggingface-gradio/lesson/5/describe-and-generate-game)**. Additional functionality was added to improve the user experience by including audio output.
