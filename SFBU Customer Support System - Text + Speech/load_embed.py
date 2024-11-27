import os
import re
import openai
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader
from langchain_community.document_loaders.blob_loaders.youtube_audio import YoutubeAudioLoader
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers.audio import OpenAIWhisperParser
from langchain_text_splitters.character import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']
embedding = OpenAIEmbeddings()
# !rm -rf ./docs/chroma
persist_directory = 'docs/chroma/'

all_documents = []

# Load PDF
pdf_loader = PyPDFLoader("docs/sfbu-2024-2025-university-catalog-8-20-2024.pdf")
pdf_pages = pdf_loader.load_and_split()
all_documents.extend([Document(page_content=page.page_content, metadata=page.metadata) for page in pdf_pages])

# Load YouTube audio
urls = ["https://www.youtube.com/watch?v=kuZNIvdwnMc"]
save_dir = "docs/youtube/"
youtube_loader = GenericLoader(YoutubeAudioLoader(urls, save_dir), OpenAIWhisperParser())
youtube_docs = youtube_loader.load()
all_documents.extend([Document(page_content=doc.page_content, metadata=doc.metadata) for doc in youtube_docs])

# Load and clean web pages
web_urls = [
    "https://www.sfbu.edu/student-health-insurance",
    "https://www.sfbu.edu/why-we-are-here",
    "https://www.sfbu.edu/admissions",
    "https://www.sfbu.edu/learning-teaching",
    "https://www.sfbu.edu/student-life-support",
    "https://www.sfbu.edu/contact-us"
]

for url in web_urls:
    web_loader = WebBaseLoader(url)
    docs = web_loader.load()
    raw_content = docs[0].page_content
    cleaned_content = re.sub(r'\n\s*\n', '\n', raw_content).strip()
    all_documents.append(Document(page_content=cleaned_content, metadata={"source": url}))

# Split documents into chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150)
splits = text_splitter.split_documents(all_documents)

# Embed and store documents in a vectorstore
vectordb = Chroma.from_documents(documents=splits, embedding=embedding, persist_directory=persist_directory)
print(f"Vectorstore created with {vectordb._collection.count()} documents.")
