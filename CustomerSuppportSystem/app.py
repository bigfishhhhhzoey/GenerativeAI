from flask import Flask, render_template, request, redirect, url_for
import os
import pandas as pd
import tiktoken
import numpy as np
from openai import OpenAI
from ast import literal_eval
from typing import List
from scipy import spatial
from embedding import generate_embeddings
from crawler import crawl_website

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("API_KEY"))

# Initialize Flask app
app = Flask(__name__)

# Load tokenizer
tokenizer = tiktoken.get_encoding("cl100k_base")

# Utility functions for embedding and question-answer logic
def distances_from_embeddings(query_embedding: List[float], embeddings: List[List[float]], distance_metric="cosine") -> List[float]:
    distance_metrics = {
        "cosine": spatial.distance.cosine,
        "L1": spatial.distance.cityblock,
        "L2": spatial.distance.euclidean,
        "Linf": spatial.distance.chebyshev,
    }
    return [distance_metrics[distance_metric](query_embedding, embedding) for embedding in embeddings]

def create_context(question: str, df: pd.DataFrame, max_len: int = 1800, model: str = "text-embedding-3-small", distance_metric: str = "cosine"):
    q_embeddings = client.embeddings.create(input=question, model=model).data[0].embedding
    df['distances'] = distances_from_embeddings(q_embeddings, df['embeddings'].tolist(), distance_metric)

    returns, cur_len = [], 0
    for _, row in df.sort_values('distances', ascending=True).iterrows():
        cur_len += row['n_tokens'] + 4
        if cur_len > max_len:
            break
        returns.append(row["text"])
    
    return "\n\n###\n\n".join(returns)

def prepare_data():
    if not os.path.exists('processed/embeddings.csv'):
        return None
    df = pd.read_csv('processed/embeddings.csv', index_col=0)
    df['embeddings'] = df['embeddings'].apply(literal_eval).apply(np.array)
    return df

def answer_question(df, question, model="gpt-4o-mini", max_len=1800, max_tokens=150):
    context = create_context(question, df, max_len)
    try:
        response = client.completions.create(
            model=model,
            prompt=f"Answer the question based on the context below, and if the question can't be answered based on the context, say 'I don't know'.\n\nContext: {context}\n\nQuestion: {question}\nAnswer:",
            temperature=0,
            max_tokens=max_tokens
        )

        answer = response.choices[0].text.strip()

        # If the answer is blank or doesn't contain useful information, return "I don't know"
        if not answer or answer.lower() in ["", "i don't know", "i don’t know"]:
            return "I don't know"
        
        return answer

    except Exception as e:
        return f"Error: {e}"

# Route to handle the home page and form submission
@app.route("/", methods=["GET", "POST"])
def index():
    question = None
    answer = None

    if request.method == "POST":
        # Get the question from the form
        question = request.form.get("question")

        # Check if the embeddings file is available
        df = prepare_data()
        if df is None:
            return render_template("index.html", question=question, answer="No embeddings found. Please run the crawler and embedding generator.")

        # Generate the answer to the question
        answer = answer_question(df, question)
    
    return render_template("index.html", question=question, answer=answer)

# Route to trigger crawling and embedding generation (optional)
@app.route("/crawl_and_generate", methods=["POST"])
def crawl_and_generate():
    # Get the website URL and limit from the form
    full_url = request.form.get("url")
    limit = int(request.form.get("limit", 10))

    # Crawl the website
    crawl_website(full_url, limit)

    # Generate embeddings
    generate_embeddings()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
