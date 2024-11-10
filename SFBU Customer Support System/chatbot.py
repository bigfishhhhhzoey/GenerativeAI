#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import openai
import sys
sys.path.append('../..')

import panel as pn  # GUI
pn.extension()

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']


# In[2]:


import bs4
import panel as pn
import param
import re
from typing import List, Sequence
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.document_loaders.blob_loaders.youtube_audio import YoutubeAudioLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers.audio import OpenAIWhisperParser
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


# In[3]:


persist_directory = 'docs/chroma/'
# !rm -rf ./docs/chroma
embedding = OpenAIEmbeddings()
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)
# print(f"Vectorstore created with {vectordb._collection.count()} documents.")


# In[4]:


llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
# llm.invoke("Hello world!")


# In[5]:


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


# In[6]:


# Define the state structure using your existing StateGraph setup
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

# Example usage
# result = app.invoke(initial_state, config=config)
# print(result["answer"])


# In[12]:


class ChatbotUI(param.Parameterized):
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

    def process_query(self, query):
        """Handles user input and appends responses to the chat history."""
        if self.is_processing or not query:
            return  # Prevent double processing or empty queries
    
        self.is_processing = True
    
        # Define the configuration required for checkpointing
        config = {"configurable": {"thread_id": "chatbot_session"}}
    
        try:
            # Invoke the chatbot with the necessary configuration
            result = app.invoke({"input": query, "chat_history": self.chat_history}, config=config)
    
            # Update chat history with HumanMessage and AIMessage
            user_message = HumanMessage(query)
            bot_message = AIMessage(result["answer"])
    
            # Only append messages if they are not already in the history
            if not (self.chat_history and self.chat_history[-2:] == [user_message, bot_message]):
                self.chat_history.append(user_message)
                self.chat_history.append(bot_message)
    
            # Update UI panels
            self.panels.extend([
                pn.Row('User:', pn.pane.Markdown(query, width=600)),
                pn.Row(
                    'ChatBot:',
                    pn.pane.Markdown(
                        f"<div style='background-color: #F6F6F6; padding: 10px;'>{result['answer']}</div>",
                        width=600
                    )
                )
            ])
        except Exception as e:
            print(f"Error processing query: {e}")
        finally:
            self.is_processing = False
    
        self.param.trigger('chat_history')  # Trigger reactivity
        return pn.WidgetBox(*self.panels, scroll=True)


    @param.depends('chat_history')
    def display_chat_history(self):
        """Displays the current chat history."""
        if not self.chat_history:
            return pn.pane.Markdown("No chat history yet.", width=600)
        
        rlist = []
        for entry in self.chat_history:
            if isinstance(entry, HumanMessage):
                rlist.append(pn.Row('User:', pn.pane.Markdown(entry.content, width=600)))
            elif isinstance(entry, AIMessage):
                rlist.append(pn.Row(
                    'ChatBot:',
                    pn.pane.Markdown(
                        f"<div style='background-color: #F6F6F6; padding: 10px;'>{entry.content}</div>",
                        width=600
                    )
                ))

        return pn.WidgetBox(*rlist, scroll=True)

    def clear_chat_history(self, event=None):
        """Clears the chat history."""
        self.chat_history.clear()
        self.panels.clear()
        self.param.trigger('chat_history')
    
    def process_pdf(self, event):
        """Process PDF upload."""
        if not self.pdf_input.value:
            self.upload_message = "Please upload a valid PDF file."
            self.document_uploaded = False
            self.param.trigger('upload_message')
            return

        self.is_processing = True
        try:
            pdf_loader = PyPDFLoader(self.pdf_input.filename)
            pdf_docs = pdf_loader.load_and_split()
            all_documents.extend([Document(page_content=page.page_content, metadata=page.metadata) for page in pdf_docs])
            
            vectordb.add_documents(pdf_docs)
            vectordb.persist()
            
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
            
            all_documents.append(doc_obj)
            vectordb.add_documents([doc_obj])
            vectordb.persist()

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
            all_documents.extend([Document(page_content=doc.page_content, metadata=doc.metadata) for doc in youtube_docs])
            
            vectordb.add_documents(youtube_docs)
            vectordb.persist()

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

# Set up actions for document upload
chatbot_ui.button_process_pdf.on_click(chatbot_ui.process_pdf)
chatbot_ui.button_process_url.on_click(chatbot_ui.process_url)
chatbot_ui.button_process_youtube.on_click(chatbot_ui.process_youtube)

# Panel UI components
inp = pn.widgets.TextInput(placeholder='Ask me a question...')
conversation = pn.bind(chatbot_ui.process_query, inp)
clear_button = pn.widgets.Button(name='Clear History', button_type='danger')
clear_button.on_click(chatbot_ui.clear_chat_history)

# Tabs
tab1 = pn.Column(
    pn.Row(inp),
    pn.layout.Divider(),
    pn.panel(conversation, loading_indicator=True, height=300)
)

tab2 = pn.Column(
    chatbot_ui.display_chat_history,
    pn.Row(clear_button)
)

tab3 = pn.Column(
    pn.Row(chatbot_ui.pdf_input, chatbot_ui.button_process_pdf),
    pn.Row(chatbot_ui.url_input, chatbot_ui.button_process_url),
    pn.Row(chatbot_ui.youtube_input, chatbot_ui.button_process_youtube),
    pn.layout.Divider(),
    chatbot_ui.get_upload_status
)

# Dashboard with three tabs
dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# Chatbot with Document Retrieval')),
    pn.Tabs(('Conversation', tab1), ('Chat History', tab2), ('Document Upload', tab3))
)

dashboard.servable()


# In[ ]:




