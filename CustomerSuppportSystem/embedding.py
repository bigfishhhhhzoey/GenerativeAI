import os
import pandas as pd
import tiktoken
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("API_KEY"))

# Ensure the API key is loaded correctly
if not client.api_key:
    raise ValueError("OpenAI API key not found. Make sure API_KEY is set as an environment variable.")

# Tokenizer initialization
tokenizer = tiktoken.get_encoding("cl100k_base")
max_tokens = 500

def split_into_many(text, max_tokens=max_tokens):
    sentences = text.split('. ')
    n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]
    
    chunks, chunk = [], []
    tokens_so_far = 0

    for sentence, token in zip(sentences, n_tokens):
        if tokens_so_far + token > max_tokens:
            chunks.append(". ".join(chunk) + ".")
            chunk = []
            tokens_so_far = 0
        if token > max_tokens:
            continue
        chunk.append(sentence)
        tokens_so_far += token + 1

    if chunk:
        chunks.append(". ".join(chunk) + ".")
    return chunks

def generate_embeddings():
    if not os.path.exists('processed/scraped.csv'):
        print("No crawled data found. Please run the crawler first.")
        return
    
    df = pd.read_csv('processed/scraped.csv', index_col=0)
    
    df['n_tokens'] = df['text'].apply(lambda x: len(tokenizer.encode(x)))
    shortened = []

    for _, row in df.iterrows():
        if row['n_tokens'] > max_tokens:
            shortened += split_into_many(row['text'])
        else:
            shortened.append(row['text'])

    df = pd.DataFrame(shortened, columns=['text'])
    df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))

    # Apply embedding
    df['embeddings'] = df.text.apply(lambda x: client.embeddings.create(input=x, model="text-embedding-ada-002").data[0].embedding)
    
    df.to_csv('processed/embeddings.csv')
    print("Embeddings generated and saved.")

if __name__ == "__main__":
    generate_embeddings()
