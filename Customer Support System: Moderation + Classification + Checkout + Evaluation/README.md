# Customer Support System: Moderation, Classification, Checkout, and Evaluation

This project is an extension of a **Customer Comment and Response Generator** app that now incorporates robust features like **moderation**, **prompt injection prevention**, **classification**, **chain of thought reasoning**, **output moderation**, and **response evaluation**. The system offers a streamlined experience for users through both a command-line interface and a Flask-based web interface.

## 1. Prerequisite App

### [Customer Comment and Response Generator](https://github.com/bigfishhhhhzoey/GenerativeAI/tree/main/Customer%20Support%20Email%20Generator/)

The previous **Customer Comment and Response Generator** app was designed to generate customer comments and email responses based on product information. It allowed users to interact with an AI model to generate feedback on electronic products. This system included:
- A user-friendly input system for providing product data
- Generation of customer comments based on that data
- Sentiment analysis and summary of customer comments
- Generation email subjects and content based on the analysis
- Support with 30 of the most commonly spoken languages

You can explore the app [here](https://github.com/bigfishhhhhzoey/GenerativeAI/tree/main/Customer%20Support%20Email%20Generator/).

---

## 2. Project Design

### Customer Support System: Moderation, Classification, Checkout, and Evaluation

This project introduces several new features to enhance the robustness of the customer support system. Here’s a breakdown of the new functionalities:

### Features

1. **Input Moderation**: Uses moderation API to ensure that input is appropriate and safe for processing. It flags inappropriate language in customer comments.
2. **Prompt Injection Prevention**: Detects potential prompt injection attacks in user inputs and halts execution to prevent malicious exploitation.
3. **Chain of Thought Reasoning**: Generates contextually appropriate and helpful chatbot responses based on the analyzed comment.
4. **Output Moderation**: After generating a chatbot response, this function checks if the output is appropriate.
5. **Evaluation**: This feature evaluates the chatbot’s response to ensure it is factually correct and satisfies the customer’s query.

---

## 3. Test Cases

Here are some test cases to test the core functionality of this app.

### Input Moderation:
For a benign comment, the system should not flag anything, but for inappropriate comments, it should detect and prevent further action.

![test](images/test_input1.png)

![test](images/test_input2.png)

### Prompt Injection Prevention:
The system should recognize common prompt injection attempts and flag them appropriately.

![test](images/test_prompt.png)

### Classification:
Properly classify customer support queries to handle different cases.

![test](images/test_class.png)

### Chain of Thought Reasoning:
Answer customer's query using chain of thought reasoning and then provide final response without the inner monologue.

![test](images/test_chain.png)

### Output Moderation: 
After generating a chatbot response, check if the output is appropriate.

![test](images/test_output1.png)

![test](images/test_output2.png)

### Output Self-Evaluation:
Check if the answer is fact-based.

![test](images/test_self_eva.png)

### Evaluation for Question with Single Right Answer
Evaluate the response to each question in the question set with its ideal answer and print out the fraction score.

![test](images/test_eva1.png)
![test](images/test_eva2.png)
![test](images/test_eva3.png)

### Evaluation for Question with Multiple Right Answers

#### Evaluation with Rubric
Use predefined guidelines to assess the quality and performance of the response.

![test](images/test_eva4.png)

#### Evaluation with Ideal Answers
Compare the response with the ideal answer.

![test](images/test_eva5.png)

![test](images/test_eva6.png)

---

## 4. Command-Line Application

The command-line application combines the features of the original customer comment and response generator with the newly added moderation, classification, and evaluation functionalities. 

### System Workflow:

1. **Generate Comments**: Users can choose to generate customer comments in one of 30 languages.
2. **Input Moderation**: The system first checks for any inappropriate or flagged content in the input.
3. **Prompt Injection Prevention**: Next, it scans for any malicious prompt injection attempts.
4. **Sentiment Analysis**: Sentiment analysis is performed on the input to understand the emotional context.
5. **Chatbot Response Generation**: A chatbot response is generated based on the sentiment and input.
6. **Output Moderation**: The response is checked to ensure it does not contain inappropriate or harmful content.
7. **Evaluation**: Finally, the response is evaluated for accuracy and completeness.

### To Run:

```bash
python3 command_line.py
```

### Sample Use Cases:

- **Input Moderation**: The system exits the program once detected inappropriate input.

  ![command](images/command1.png)
  
- **Prompt Injection Prevention**: The system exits the program once detected prompt injection.
  
  ![command](images/command2.png)
  
- **Appropriate Input and Response**: The application analyzes the sentiment of the comment and generates an appropriate chatbot response.
  
  ![command](images/command3.png)
  ![command](images/command4.png)

---

## 5. Flask Web App

The Flask web application provides a user-friendly interface for interacting with the customer support system.

### Features:
- **Comment Input**: Users can either input their own comments or generate a comment in their preferred language (from the top 30 languages).
- **Language Selection**: Both the comment and chatbot response can be generated in one of 30 commonly spoken languages.
- **Moderation and Prompt Injection**: The app checks for inappropriate content or prompt injection attempts before processing the input.
- **Sentiment Analysis and Response**: Once the comment passes moderation, the system generates a chatbot response based on the sentiment analysis.
- **Output Moderation and Evaluation**: The system checks the response for appropriateness and evaluates its accuracy.
- **Go Back Option**: Users can review the generated responses and then go back to the main page to input new comments.

### To Run the Flask App:

1. Install dependencies:
   ```bash
   pip install flask
   ```

2. Run the Flask app:
   ```bash
   flask run
   ```

3. Access the app at `http://127.0.0.1:5000/` in your browser.

### Flask Web App Interface:

- **Step-by-Step Interaction**: Each step of the process (input moderation, sentiment analysis, response generation, etc.) is shown to the user with clear feedback.
- **Go Back Button**: After viewing the results, users can return to the home page to try new comments.

### Sample Use Cases:
- Use generated customer commment.

  ![web](images/web1.png)
  ![web](images/web2.png)

- Enter user's own question.

  ![web](images/web3.png)
  ![web](images/web4.png)

---

## Repository Link
You can access the full codebase on GitHub: [Customer Support System: Moderation + Classification + Checkout + Evaluation](https://github.com/bigfishhhhhzoey/GenerativeAI/tree/main/Customer%20Support%20System%3A%20Moderation%20%2B%20Classification%20%2B%20Checkout%20%2B%20Evaluation).

## Google Slides
You can access the presentation on Google Slides: [Customer Support System: Moderation, Classification, Checkout, Evaluation](https://docs.google.com/presentation/d/1aNkuirDzg4_AexxwBFSkM9xpe6tSp32pVLcn5gMjke0/edit?usp=sharing).
