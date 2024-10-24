# Describe-and-Generate Game

This project is a simple **Describe-and-Generate game** built using Python, Hugging Face API, and Gradio. It allows users to upload an image, generate a caption for the image (using Image-to-Text), and use that caption to generate new images (using Text-to-Image). This interactive game helps in understanding how AI models can be used to describe images and generate new content based on those descriptions.

## Features

1. **Image-to-Text Captioning**: Upload an image, and the app will generate a descriptive caption using a pre-trained Hugging Face model.
2. **Text-to-Image Generation**: Based on the generated caption or a custom text prompt, the app generates a new image.
3. **Combined Workflow**: Upload an image, generate a caption, and then automatically generate a new image based on the caption—all in one step.

## How It Works

1. **Image-to-Text (ITT)**: Converts an uploaded image into a descriptive caption using a Hugging Face model.
2. **Text-to-Image (TTI)**: Converts a text description (prompt) into an image using Hugging Face's text-to-image generation API.

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
pip install gradio requests pillow python-dotenv
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
python your_app.py
```

The app will launch in your web browser, and you can start uploading images and generating captions and new images.

## How to Play

1. Upload an image.
2. Click **Generate Caption** to generate a textual description of the image.
3. Click **Generate Image** to create a new image based on the generated caption.
4. Alternatively, use the **Caption and Generate** button to do both steps in one go!

## Example Workflow

1. Upload an image (e.g., a picture of a cat).
2. The app generates a caption like *"A cute orange tabby cat sitting on a windowsill."*
3. Based on this caption, the app generates a new image—perhaps of another cat in a similar pose.

## Project Files

- **`your_app.py`**: Main script for running the Gradio app.
- **`.env`**: Environment file containing Hugging Face API key and model endpoints.

## Resources

- [Hugging Face Gradio Lesson](https://learn.deeplearning.ai/courses/huggingface-gradio/lesson/5/describe-and-generate-game)
