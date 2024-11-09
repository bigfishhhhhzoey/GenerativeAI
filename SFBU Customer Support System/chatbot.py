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
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
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


# In[7]:


class ChatbotUI(param.Parameterized):
    chat_history = param.List(default=[])
    panels = param.List(default=[])
    is_processing = param.Boolean(default=False)  # Prevents double execution

    def process_query(self, query):
        """Handles user input and appends responses to the chat history."""
        if self.is_processing or not query:
            return  # Prevent double processing or empty queries

        self.is_processing = True

        # Invoke the chatbot
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
        self.param.trigger('chat_history')  # Trigger reactivity
        self.is_processing = False

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

# Initialize the chatbot UI
chatbot_ui = ChatbotUI()

# Panel UI components
inp = pn.widgets.TextInput(placeholder='Ask me a question...')
conversation = pn.bind(chatbot_ui.process_query, inp)

# Button to clear chat history
clear_button = pn.widgets.Button(name='Clear History', button_type='danger')
clear_button.on_click(chatbot_ui.clear_chat_history)

# Layout for Conversation tab
tab1 = pn.Column(
    pn.Row(inp),
    pn.layout.Divider(),
    pn.panel(conversation, loading_indicator=True, height=300),
)

# Layout for Chat History tab with Clear History button
tab2 = pn.Column(
    pn.panel(chatbot_ui.display_chat_history),
    pn.Row(clear_button)
)

# Dashboard
dashboard = pn.Column(
    pn.Row(pn.pane.Markdown('# Chatbot with Document Retrieval')),
    pn.Tabs(('Conversation', tab1), ('Chat History', tab2))
)

dashboard.servable()


# In[ ]:




