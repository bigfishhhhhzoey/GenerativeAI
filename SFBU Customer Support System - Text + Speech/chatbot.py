import os
import tempfile
import openai
import sys
import time
import queue
import threading
import ssl
import re
from typing import List
from pathlib import Path
from datetime import datetime
from pydub import AudioSegment
from pydub.playback import play
import speech_recognition as sr
import panel as pn  # GUI
import param
from dotenv import load_dotenv, find_dotenv
from openai import OpenAI
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.document_loaders.blob_loaders.youtube_audio import YoutubeAudioLoader
from langchain_community.document_loaders.parsers.audio import OpenAIWhisperParser
from langchain_community.document_loaders.generic import GenericLoader
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
import urllib3
import warnings

pn.extension()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
ssl._create_default_https_context = ssl._create_unverified_context

_ = load_dotenv(find_dotenv())  # read local .env file

openai.api_key = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

persist_directory = 'docs/chroma/'
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
retriever = vectordb.as_retriever()

### Contextualize question ###
contextualize_q_system_prompt = (
    "Given a chat history and the latest user question "
    "which might reference context in the chat history, "
    "formulate a standalone question which can be understood "
    "without the chat history. Do NOT answer the question, "
    "just reformulate it if needed and otherwise return it as is."
)
contextualize_q_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
history_aware_retriever = create_history_aware_retriever(
    llm, retriever, contextualize_q_prompt
)

### Answer question ###
system_prompt = (
    "You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say "
    "'I don't know.' Use three sentences maximum and keep the "
    "answer concise."
    "\n\n"
    "{context}"
)
qa_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ]
)
question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)

rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

class State(TypedDict):
    input: str
    chat_history: List[BaseMessage]
    context: str
    answer: str

# Your existing StateGraph and MemorySaver setup
def call_model(state: State):
    # Ensure 'chat_history' is initialized if it's missing
    if "chat_history" not in state:
        state["chat_history"] = []

    # Prepare the input for the rag_chain with the chat history
    response = rag_chain.invoke({
        "input": state["input"],
        "chat_history": state["chat_history"]
    })
    
    # Update the state with the new AI response
    state["chat_history"].append(HumanMessage(content=state["input"]))
    state["chat_history"].append(AIMessage(content=response["answer"]))
    
    return {
        "chat_history": state["chat_history"],
        "context": response["context"],
        "answer": response["answer"]
    }

workflow = StateGraph(state_schema=State)
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Initialize memory saver
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

config = {"configurable": {"thread_id": "abc123"}}

# Initialize the default state with an empty chat history
initial_state = {
    "input": "",
    "chat_history": [],
    "context": "",
    "answer": ""
}

# Speech Input/Output Configuration
def initialize_flags():
    global shutdown_event, pause_event
    shutdown_event = threading.Event()
    pause_event = threading.Event()

def record_audio(audio_queue, energy, pause, dynamic_energy, verbose):
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.dynamic_energy_threshold = dynamic_energy

    with sr.Microphone(sample_rate=16000) as source:
        print("Listening...")
        while not shutdown_event.is_set():
            try:
                audio = r.listen(source)
                audio_data = audio.get_wav_data()  # Get audio data in WAV format
                audio_queue.put_nowait(audio_data)
            except sr.WaitTimeoutError:
                if verbose:
                    print(f"[{datetime.now()}] Timeout: No speech detected.")
            except Exception as e:
                if shutdown_event.is_set():
                    break
                print(f"[{datetime.now()}] Error in record_audio: {e}")

# Transcribe speech to text
def transcribe_forever(audio_queue, result_queue, wake_word, verbose):
    stop_word = "stop"  # Define the stop word
    conversation_active = False  # Reset conversation mode at the start
    while not shutdown_event.is_set():
        try:
            audio_data = audio_queue.get(timeout=1)  # Timeout prevents indefinite blocking
        except queue.Empty:
            continue  # Skip if queue is empty and re-check shutdown_event

        # Save the audio to a temporary file for transcription
        temp_audio_path = "temp_audio.wav"
        with open(temp_audio_path, "wb") as temp_audio_file:
            temp_audio_file.write(audio_data)

        try:
            with open(temp_audio_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file
                )
            predicted_text = transcription.text
        except Exception as e:
            if verbose:
                print(f"[{datetime.now()}] ERROR in transcription: {e}")
            continue
        finally:
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

        if verbose:
            print(f"[{datetime.now()}] Transcription result: '{predicted_text}'")

        # Check for stop word
        if stop_word in predicted_text.strip().lower():
            if verbose:
                print(f"[{datetime.now()}] Stop word detected. Ending conversation.")
            conversation_active = False  # Exit conversation mode
            continue

        # Handle wake word or active conversation
        if conversation_active or predicted_text.strip().lower().startswith(wake_word.strip().lower()):
            if not conversation_active:  # Transition to conversation mode
                pattern = re.compile(re.escape(wake_word), re.IGNORECASE)
                predicted_text = pattern.sub("", predicted_text).strip()
                conversation_active = True
                if verbose:
                    print(f"[{datetime.now()}] Wake word detected. Starting conversation mode.")

            predicted_text = re.sub(r"[^\w\s]", "", predicted_text)  # Clean up punctuation
            if verbose:
                print(f"[{datetime.now()}] Processing input: '{predicted_text}'")

            result_queue.put_nowait(predicted_text)
        else:
            if verbose:
                print(f"[{datetime.now()}] Ignoring input (not in conversation mode).")

# Generate speech from text and play the response
def play_speech_response(response, verbose):
    try:
        speech_file_path = Path("reply.mp3")
        tts_response = client.audio.speech.create(
            model="tts-1",
            voice="shimmer",
            input=response
        )
        tts_response.stream_to_file(speech_file_path)

        reply_audio = AudioSegment.from_file(speech_file_path)
        play(reply_audio)  # Blocking playback
        if verbose:
            print(f"[{datetime.now()}] Playback completed.")
        os.remove(speech_file_path)
        if verbose:
            print(f"[{datetime.now()}] Temporary audio file 'reply.mp3' removed.")
    except Exception as e:
        if verbose:
            print(f"[{datetime.now()}] ERROR in TTS or playback: {e}")

# Add functionality to UI components for speech interaction
class ChatbotUI(param.Parameterized):
    use_speech = param.Boolean(default=False, doc="Enable speech input/output")
    chat_history = param.List(default=[])
    panels = param.List(default=[])
    is_processing = param.Boolean(default=False)
    document_uploaded = param.Boolean(default=False)
    upload_message = param.String(default="No document uploaded yet.")

    # File and URL inputs
    pdf_input = pn.widgets.FileInput(accept='.pdf')
    url_input = pn.widgets.TextInput(placeholder='Enter URL...')
    youtube_input = pn.widgets.TextInput(placeholder='Enter YouTube link...')
    
    # Buttons
    button_process_pdf = pn.widgets.Button(name='Process PDF', button_type='primary')
    button_process_url = pn.widgets.Button(name='Process URL', button_type='primary')
    button_process_youtube = pn.widgets.Button(name='Process YouTube', button_type='primary')

    def __init__(self, **params):
        super().__init__(**params)
        # Link buttons to their respective methods
        self.button_process_pdf.on_click(self.process_pdf)
        self.button_process_url.on_click(self.process_url)
        self.button_process_youtube.on_click(self.process_youtube)
        self.inp = pn.widgets.TextInput(placeholder='Ask me a question...', width=500)
        self.clear_button = pn.widgets.Button(name='Clear History', button_type='danger')
        self.clear_button.on_click(self.clear_chat_history)
        self.send_button = pn.widgets.Button(name='Send', button_type='primary')
        self.send_button.on_click(self.handle_send_button)
        self.new_conversation_button = pn.widgets.Button(name='Start New Conversation', button_type='warning')
        self.new_conversation_button.on_click(self.start_new_conversation)
        self.use_speech_toggle = pn.widgets.Toggle(name='Use Speech Input/Output', value=False)
        self.use_speech_toggle.param.watch(self.toggle_speech, 'value')
        self.inp.param.watch(self.handle_text_input, 'value')
    
    def handle_text_input(self, event):
        if event.new:
            self.process_query(event.new)
            self.inp.value = ''  # Clear input after processing
    
    def handle_send_button(self, event):
        if self.inp.value:
            self.process_query(self.inp.value)
            self.inp.value = ''

    def toggle_speech(self, event):
        self.use_speech = event.new

        if self.use_speech:
            # Initialize the flags
            initialize_flags()

            # Start threads for recording and transcribing audio
            self.audio_queue = queue.Queue()
            self.result_queue = queue.Queue()

            # Start recording and transcribing threads
            self.record_thread = threading.Thread(target=record_audio, args=(self.audio_queue, 300, 0.8, False, True))
            self.transcribe_thread = threading.Thread(target=transcribe_forever, args=(self.audio_queue, self.result_queue, "hey computer", True))

            self.record_thread.start()
            self.transcribe_thread.start()

            # Start a thread to listen for transcription results and process them as queries
            self.reply_thread = threading.Thread(target=self.process_speech_input)
            self.reply_thread.start()

        else:
            # Stop recording and transcribing threads
            shutdown_event.set()  # Signal all threads to stop

    def process_speech_input(self):
        while not shutdown_event.is_set():
            try:
                # Get the transcribed text from the result queue
                query = self.result_queue.get(timeout=1)  # Timeout prevents indefinite blocking
                if query:
                    # Process the transcribed query as if it were user input
                    self.process_query(query)
            except queue.Empty:
                continue  # Skip if queue is empty and re-check shutdown_event

    def start_new_conversation(self, event):
        self.panels.clear()
        self.param.trigger('panels')

    def process_query(self, query):
        if self.is_processing or not query:
            return  # Prevent double processing or empty queries

        self.is_processing = True

        config = {"configurable": {"thread_id": "chatbot_session"}}
        try:
            # Invoke the model to get the response
            result = app.invoke({"input": query, "chat_history": self.chat_history}, config=config)
            response_text = result["answer"]

            # Update UI panels for the conversation tab
            self.panels.append(pn.Row('User:', pn.pane.Markdown(query, width=510)))
            self.panels.append(pn.Row('ChatBot:', pn.pane.Markdown(f"<div style='background-color: #F6F6F6; padding: 10px;'>{response_text}</div>", width=510)))

            # Trigger UI update to display the conversation immediately
            self.param.trigger('panels')

            # If speech is enabled, play the response after updating the UI
            if self.use_speech:
                play_speech_response(response_text, verbose=True)

        except Exception as e:
            print(f"Error processing query: {e}")
        finally:
            self.is_processing = False
        
        self.param.trigger('chat_history')
        return pn.WidgetBox(*self.panels, scroll=True)
        

    @param.depends('panels')
    def display_conversation(self):
        """Displays the current conversation in the conversation tab."""
        if not self.panels:
            return pn.pane.Markdown("No conversation yet.", width=550)
        return pn.Column(*self.panels, scroll=True)

    @param.depends('chat_history')
    def display_chat_history(self):
        if not self.chat_history:
            return pn.pane.Markdown("No chat history yet.", width=550)
        
        rlist = []
        for entry in self.chat_history:
            if isinstance(entry, HumanMessage):
                rlist.append(pn.Row('User:', pn.pane.Markdown(entry.content, width=500)))
            elif isinstance(entry, AIMessage):
                rlist.append(pn.Row('ChatBot:', pn.pane.Markdown(f"<div style='background-color: #F6F6F6; padding: 10px;'>{entry.content}</div>", width=500)))
        
        return pn.Column(*rlist, scroll=True)

    def clear_chat_history(self, event=None):
        self.chat_history.clear()
        self.panels.clear()
        self.param.trigger('chat_history')
    
    def process_pdf(self, event):
        """Process PDF upload."""
        if not self.pdf_input.value or not self.pdf_input.filename.endswith(".pdf"):
            self.upload_message = "❌ Please upload a valid PDF file."
            self.document_uploaded = False
            self.param.trigger('upload_message')
            return
    
        self.is_processing = True
        try:
            # Save the uploaded PDF file to a temporary path
            temp_file_path = tempfile.mktemp(suffix=".pdf")
            with open(temp_file_path, "wb") as temp_file:
                temp_file.write(self.pdf_input.value)
    
            # Load and split the PDF using PyPDFLoader
            pdf_loader = PyPDFLoader(temp_file_path)
            pdf_docs = pdf_loader.load_and_split()
            
            # Add documents to the vector store
            vectordb.add_documents(pdf_docs)
    
            # Update the upload message
            self.upload_message = "✅ PDF uploaded and processed successfully."
            self.document_uploaded = True
    
        except Exception as e:
            self.upload_message = f"❌ Error processing PDF: {e}"
            self.document_uploaded = False
        finally:
            self.is_processing = False
            self.param.trigger('upload_message')

    def process_url(self, event):
        """Process URL input."""
        url = self.url_input.value
        if not url:
            self.upload_message = "Please enter a valid URL."
            self.document_uploaded = False
            self.param.trigger('upload_message')
            return
    
        self.is_processing = True
        try:
            web_loader = WebBaseLoader(url)
            docs = web_loader.load()
            cleaned_content = re.sub(r'\n\s*\n', '\n', docs[0].page_content).strip()
            doc_obj = Document(page_content=cleaned_content, metadata={"source": url})
            
            # Add the document directly to vectordb
            vectordb.add_documents([doc_obj])
            
            # Clear the URL input after processing
            self.url_input.value = ""

            # Update the upload message
            self.upload_message = "✅ URL content uploaded and processed successfully."
            self.document_uploaded = True
        except Exception as e:
            self.upload_message = f"❌ Error processing URL: {e}"
            self.document_uploaded = False
        finally:
            self.is_processing = False
            self.param.trigger('upload_message')
    
    def process_youtube(self, event):
        """Process YouTube link."""
        youtube_url = self.youtube_input.value
        if not youtube_url:
            self.upload_message = "Please enter a valid YouTube link."
            self.document_uploaded = False
            self.param.trigger('upload_message')
            return
    
        self.is_processing = True
        try:
            youtube_loader = GenericLoader(YoutubeAudioLoader([youtube_url], "docs/youtube/"), OpenAIWhisperParser())
            youtube_docs = youtube_loader.load()
            # Add YouTube docs directly to vectordb
            vectordb.add_documents(youtube_docs)

            # Clear the YouTube input after processing
            self.youtube_input.value = ""

            # Update the upload message
            self.upload_message = "✅ YouTube video content uploaded and processed successfully."
            self.document_uploaded = True           
        except Exception as e:
            self.upload_message = f"❌ Error processing YouTube link: {e}"
            self.document_uploaded = False
        finally:
            self.is_processing = False
            self.param.trigger('upload_message')

    @param.depends('upload_message')
    def get_upload_status(self):
        """Displays the status of the document upload."""
        return pn.pane.Markdown(self.upload_message, width=600)
    
    
# Instantiate the Chatbot UI
chatbot_ui = ChatbotUI()

# Dashboard tabs updated with speech toggle
tab1 = pn.Column(
    pn.panel(chatbot_ui.display_conversation, loading_indicator=True, width=600, height=300),
    pn.Row(chatbot_ui.inp, pn.layout.HSpacer(), chatbot_ui.send_button, width=600),
    pn.Row(chatbot_ui.use_speech_toggle, pn.layout.HSpacer(), chatbot_ui.new_conversation_button, width=600)
)

tab2 = pn.Column(
    chatbot_ui.display_chat_history,
    pn.Row(chatbot_ui.clear_button)
)

tab3 = pn.Column(
    pn.Row(chatbot_ui.pdf_input, chatbot_ui.button_process_pdf),
    pn.Row(chatbot_ui.url_input, chatbot_ui.button_process_url),
    pn.Row(chatbot_ui.youtube_input, chatbot_ui.button_process_youtube),
    pn.layout.Divider(),
    chatbot_ui.get_upload_status
)

dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# SFBU Customer Support System')),
    pn.Tabs(('Conversation', tab1), ('Chat History', tab2), ('Document Upload', tab3))
)

dashboard.servable()
