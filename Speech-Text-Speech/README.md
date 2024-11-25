# Speech-to-Text-to-Speech Projects

This directory contains two projects that demonstrate advanced **speech-to-text-to-speech (STT)** capabilities using **OpenAI GPT-4**, **Whisper API**, and text-to-speech tools. Each project features a conversational voice assistant designed to handle user queries, generate responses using AI, and output them via natural-sounding audio playback.

## Projects Overview

1. **GTTS Project**:
   - Integrates **GPT-4o-mini**, **Whisper API**, and **Google TTS (gTTS)** for efficient and cost-effective voice interactions.
   - Offers **threaded mode** for simultaneous recording, transcription, and response generation, as well as a **linear mode** for sequential processing.
   - **[Explore the GTTS Project](./GTTS)**

2. **OpenAI TTS Project**:
   - Builds on the GTTS project, replacing gTTS with **OpenAI TTS** for higher-quality audio output.
   - Supports the same threaded and linear modes, with additional improvements for resource management and audio playback.
   - **[Explore the OpenAI TTS Project](./OpenAI%20TTS)**

## Key Features
- Wake word and stop word support for natural conversation flow.
- Verbose and default logging modes for debugging and user-friendly interaction.
- Graceful shutdown mechanisms to ensure smooth resource cleanup.

## Getting Started
Refer to the individual project directories for setup instructions and usage examples:
- **[GTTS Project](./GTTS)**
- **[OpenAI TTS Project](./OpenAI%20TTS)**
