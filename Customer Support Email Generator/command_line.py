from openai import OpenAI
import os
import argparse
from products import products
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_completion(messages, model="gpt-4o-mini", temperature=0.3):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content


def generate_customer_comment(products_data):
    """
    Generate customer comment with provided products_data
    """
    system_message = f"""Assume that you are a customer to an electronic product company.\
The products' are delimited by triple backticks.\
Products: ```{products_data}```"""
    
    user_message = "Provide a 100-word comment regarding the products."
    
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return get_completion(messages)


def generate_email_subject(comment):
    """
    Generate email subject with provided customer comment about a product.
    """
    system_message = f"""Assume you provide customer support for an electronic product company.\
The comment is delimited by triple backticks.\
```{comment}```"""
    
    user_message = "Generate an email subject based on the comment."
    
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return get_completion(messages)


def generate_summary(comment):
    """
    Generate the summary of the customer's comment
    """
    system_message = f"""Assume you provide customer support for an electronic product company.\
Summarize the comment, delimited by triple backticks.\
```{comment}```"""
    
    user_message = "Generate a summary of the comment."
    
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return get_completion(messages)


def analyze_sentiment(comment):
    """
    Analyze Customer Comment Sentiment
    Return Positive or Negative
    """
    system_message = f"""Assume you provide customer support for an electronic product company.\
The comment is delimited by triple backticks.\
```{comment}```"""
    
    user_message = "Perform sentiment analysis on the comment."
    
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    sentiment = get_completion(messages)
    return sentiment.strip().capitalize()  # Return the sentiment analysis result


def generate_email(comment, subject, summary, sentiment, language):
    """
    Generate a response email based on the customer comment and sentiment analysis.
    """
    system_message = f"""You are a customer service representative.\
The following contains the customer comment, email subject, summary, and sentiment analysis, delimited by triple backticks.\
1. Comment: ```{comment}```\
2. Subject: ```{subject}```\
3. Summary: ```{summary}```\
4. Sentiment: ```{sentiment}```"""
    
    user_message = f"Generate a professional email in {language} based on the provided information."
    
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]
    return get_completion(messages)


def main():
    parser = argparse.ArgumentParser(description="Customer Service Email Generation")
    # Remove the language argument from the parser to prompt user instead
    args = parser.parse_args()
    
    # Ask the user to input the desired language
    language = input("Please enter the language for the email (e.g., English, Spanish, French): ")
    
    # Generate comment
    comment = generate_customer_comment(products)
    print(f"Customer Comment:\n{comment}\n")
    
    # Generate email subject
    subject = generate_email_subject(comment)
    print(f"Email Subject:\n{subject}\n")
    
    # Generate summary
    summary = generate_summary(comment)
    print(f"Summary of Comment:\n{summary}\n")
    
    # Analyze sentiment
    sentiment = analyze_sentiment(comment)
    print(f"Sentiment Analysis:\n{sentiment}\n")
    
    # Generate email
    email = generate_email(comment, subject, summary, sentiment, language)
    print(f"Generated Email:\n{email}\n")

if __name__ == '__main__':
    main()
