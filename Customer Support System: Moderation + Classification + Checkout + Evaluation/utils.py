from collections import defaultdict
from products import products
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
delimiter = '```'

# Load environment variables from .env file
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_completion(
        messages,
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=500,
    ): 
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content


def generate_customer_comment(products_data):
    """
    Generate customer comment with provided products_data
    """
    system_message = f"""Assume that you are a customer to an electronic product company.\
The products' are delimited with by tripe backticks.\
Products: {delimiter}{products_data}{delimiter}\
"""

    user_message = f"""
    Provide a 100-word comment regarding the products.
    """
    prompt = [
        {'role' : 'system', 'content' : system_message},
        {'role' : 'user', 'content' : f"{delimiter}{user_message}{delimiter}"},
        {'role' : 'assistant', 'content': 'talk as a customer' }
    ]
    response = get_completion(prompt)
    return response


# Input Moderation
def input_moderation(comment):
    response = client.moderations.create(input=comment)
    moderation_output = response.results[0]
    return moderation_output.to_dict()
    

def input_flagged(moderation_output):
    flagged = moderation_output['flagged']
    if flagged:
        return "The response is not appropriate!"
    else:
        return "The response is appropriate!"


# Prevent Prompt Injection
def prompt_injection(user_input):
    system_message = f"""
    Assume that you provide customer support for an electronic product company. \
    Assistant responses must be related with electronic products. \
    If the user says something other than electronic products, \
    say 'Sorry, I can not help with that.' The user input \
    message will be delimited with {delimiter} characters.
    """
    user_message = f"""
    {delimiter}{user_input}{delimiter}
    """

    messages =  [  
        {'role':'system', 'content': system_message},    
        {'role':'user', 'content': user_message}
    ] 
    return get_completion(messages)


# Classification
def get_classification(user_input):
    system_message = f"""
    You will be provided with customer service queries. 
    The customer service query will be delimited with {delimiter} characters.
    Classify each query into a primary category and a secondary category. 
    Provide your output in json format with the keys: primary and secondary. 
    Don't add any extra delimiter in the beginning or the end.

    Primary categories: Billing, Technical Support, \
    Account Management, or General Inquiry.

    Billing secondary categories:
    Unsubscribe or upgrade
    Add a payment method
    Explanation for charge
    Dispute a charge

    Technical Support secondary categories:
    General troubleshooting
    Device compatibility
    Software updates

    Account Management secondary categories:
    Password reset
    Update personal information
    Close account
    Account security

    General Inquiry secondary categories:
    Product information
    Pricing
    Feedback
    Speak to a human
    """
    messages =  [  
        {'role':'system', 'content': system_message},    
        {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"}
    ] 
    return get_completion(messages)


# Chain of Thoughts Reasoning
def chain_of_thought_reasoning(user_input):
    system_message = f"""
    Follow these steps to answer the customer queries.
    The customer query will be delimited with 3 backtick,\
    i.e. {delimiter}. 

    # Step 1: deciding the type of inquiry
    Step 1:{delimiter} First decide whether the user is \
    asking a question about a specific product or products. \

    Product cateogry doesn't count. 

    # Step 2: identifying specific products
    Step 2:{delimiter} If the user is asking about \
    specific products, identify whether \
    the products are in the following list.
    All available products: 
    1. Product: TechPro Ultrabook
    Category: Computers and Laptops
    Brand: TechPro
    Model Number: TP-UB100
    Warranty: 1 year
    Rating: 4.5
    Features: 13.3-inch display, 8GB RAM, 256GB SSD, 
                Intel Core i5 processor
    Description: A sleek and lightweight ultrabook for 
                    everyday use.
    Price: $799.99

    2. Product: BlueWave Gaming Laptop
    Category: Computers and Laptops
    Brand: BlueWave
    Model Number: BW-GL200
    Warranty: 2 years
    Rating: 4.7
    Features: 15.6-inch display, 16GB RAM, 512GB SSD, 
                NVIDIA GeForce RTX 3060
    Description: A high-performance gaming laptop for an 
                immersive experience.
    Price: $1199.99

    3. Product: PowerLite Convertible
    Category: Computers and Laptops
    Brand: PowerLite
    Model Number: PL-CV300
    Warranty: 1 year
    Rating: 4.3
    Features: 14-inch touchscreen, 8GB RAM, 256GB SSD, 
                360-degree hinge
    Description: A versatile convertible laptop with a 
                responsive touchscreen.
    Price: $699.99

    4. Product: TechPro Desktop
    Category: Computers and Laptops
    Brand: TechPro
    Model Number: TP-DT500
    Warranty: 1 year
    Rating: 4.4
    Features: Intel Core i7 processor, 16GB RAM, 1TB HDD, 
                NVIDIA GeForce GTX 1660
    Description: A powerful desktop computer for work 
                and play.
    Price: $999.99

    5. Product: BlueWave Chromebook
    Category: Computers and Laptops
    Brand: BlueWave
    Model Number: BW-CB100
    Warranty: 1 year
    Rating: 4.1
    Features: 11.6-inch display, 4GB RAM, 32GB eMMC, 
                Chrome OS
    Description: A compact and affordable Chromebook for 
                everyday tasks.
    Price: $249.99

    # Step 3: listing assumptions
    Step 3:{delimiter} If the message contains products \
    in the list above, list any assumptions that the \
    user is making in their \
    message e.g. that Laptop X is bigger than \
    Laptop Y, or that Laptop Z has a 2 year warranty.

    # Step 4: providing corrections
    Step 4:{delimiter}: If the user made any assumptions, \
    figure out whether the assumption is true based on your \
    product information. 

    # Step 5
    Step 5:{delimiter}: First, politely correct the \
    customer's incorrect assumptions if applicable. \
    Only mention or reference products in the list of \
    5 available products, as these are the only 5 \
    products that the store sells. \
    
    Answer the customer in a friendly tone.
    Use the following format:
    Step 1:{delimiter} <step 1 reasoning>
    Step 2:{delimiter} <step 2 reasoning>
    Step 3:{delimiter} <step 3 reasoning>
    Step 4:{delimiter} <step 4 reasoning>
    Response to user:{delimiter} <response to customer>
    """

    messages =  [  
        {'role':'system', 'content': system_message},    
        {'role':'user', 'content': f"{delimiter}{user_input}{delimiter}"},  
    ] 
    response = get_completion(messages)
    return response


# Check Output
def output_moderation(output):
    response = client.moderations.create(input=output)
    moderation_output = response.results[0]
    return moderation_output.to_dict()


def output_flagged(moderation_output):
    flagged = moderation_output['flagged']
    if flagged:
        return "The answer is not appropriate!"
    else:
        return "The answer is appropriate!"


def self_evaluate_output(customer_message, final_response_to_customer):
    system_message = f"""
You are an assistant that evaluates whether \
customer service agent responses sufficiently \
answer customer questions, and also validates that \
all the facts the assistant cites from the product \
information are correct.
The product information and user and customer \
service agent messages will be delimited by \
3 backticks, i.e. ```.
Respond with a Y or N character, with no punctuation:
Y - if the output sufficiently answers the question \
AND the response correctly uses product information \
N - otherwise \
Output a single letter only.
    """
    product_information = """{ "name": "SmartX ProPhone", "category": "Smartphones and Accessories", "brand": "SmartX", "model_number": "SX-PP10", "warranty": "1 year", "rating": 4.6, "features": [ "6.1-inch display", "128GB storage", "12MP dual camera", "5G" ], "description": "A powerful smartphone with advanced camera features.", "price": 899.99 } { "name": "FotoSnap DSLR Camera", "category": "Cameras and Camcorders", "brand": "FotoSnap", "model_number": "FS-DSLR200", "warranty": "1 year", "rating": 4.7, "features": [ "24.2MP sensor", "1080p video", "3-inch LCD", "Interchangeable lenses" ], "description": "Capture stunning photos and videos with this versatile DSLR camera.", "price": 599.99 } { "name": "CineView 4K TV", "category": "Televisions and Home Theater Systems", "brand": "CineView", "model_number": "CV-4K55", "warranty": "2 years", "rating": 4.8, "features": [ "55-inch display", "4K resolution", "HDR", "Smart TV" ], "description": "A stunning 4K TV with vibrant colors and smart features.", "price": 599.99 } { "name": "SoundMax Home Theater", "category": "Televisions and Home Theater Systems", "brand": "SoundMax", "model_number": "SM-HT100", "warranty": "1 year", "rating": 4.4, "features": [ "5.1 channel", "1000W output", "Wireless subwoofer", "Bluetooth" ], "description": "A powerful home theater system for an immersive audio experience.", "price": 399.99 } { "name": "CineView 8K TV", "category": "Televisions and Home Theater Systems", "brand": "CineView", "model_number": "CV-8K65", "warranty": "2 years", "rating": 4.9, "features": [ "65-inch display", "8K resolution", "HDR", "Smart TV" ], "description": "Experience the future of television with this stunning 8K TV.", "price": 2999.99 } { "name": "SoundMax Soundbar", "category": "Televisions and Home Theater Systems", "brand": "SoundMax", "model_number": "SM-SB50", "warranty": "1 year", "rating": 4.3, "features": [ "2.1 channel", "300W output", "Wireless subwoofer", "Bluetooth" ], "description": "Upgrade your TV's audio with this sleek and powerful soundbar.", "price": 199.99 } { "name": "CineView OLED TV", "category": "Televisions and Home Theater Systems", "brand": "CineView", "model_number": "CV-OLED55", "warranty": "2 years", "rating": 4.7, "features": [ "55-inch display", "4K resolution", "HDR", "Smart TV" ], "description": "Experience true blacks and vibrant colors with this OLED TV.", "price": 1499.99 }"""

    q_a_pair = f"""
Customer message: ```{customer_message}```
Product information: ```{product_information}```
Agent response: ```{final_response_to_customer}```

Does the response use the retrieved information correctly?
Does the response sufficiently answer the question?

Output Y or N
"""
    # print(q_a_pair)
    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': q_a_pair}
    ]

    response = get_completion(messages, max_tokens=1)
    if response == 'Y':
        return "The answer is factually based!"
    else:
        return "The answer is not factually based!"
    

# Further modify the model by adding a new few-shot learning case
def find_category_and_product_v3(user_input,products_and_category):
    system_message = f"""
    You will be provided with customer service queries. \
The customer service query will be delimited with {delimiter} characters.
Output a python list of json objects, where each object has the following format:
'category': <one of Computers and Laptops, Smartphones 
and Accessories, \
Televisions and Home Theater Systems, \
Gaming Consoles and Accessories, Audio Equipment, Cameras \
and Camcorders>,
AND
'products': <a list of products that must be found in the \
allowed products below>
Do not output any additional text that is not in JSON format.
Do not write any explanatory text after outputting the 
requested JSON.

Where the categories and products must be found in the \
customer service query. \
If a product is mentioned, it must be associated with the correct \
category in the allowed products list below.
If no products or categories are found, output an empty list.

List out all products that are relevant to the customer service 
query based on how closely it relates
to the product name, category and description.
Do not assume, from the name of the product, any features or 
attributes such as relative quality or price.

The allowed products are provided in JSON format.
The keys of each item represent the category.
The values of each item is a list of products that are within 
that category.
Allowed products: {products_and_category}
"""
  
    few_shot_user_1 = """I want the most expensive computer. What do you recommend?"""
    few_shot_assistant_1 = """ 
    [{'category': 'Computers and Laptops', 
      'products': ['TechPro Ultrabook', 'BlueWave Gaming Laptop', 
           'PowerLite Convertible', 
      'TechPro Desktop', 'BlueWave Chromebook']}]
    """
    
    few_shot_user_2 = """I want the cheapest computer. What do you recommend?"""
    few_shot_assistant_2 = """ 
    [{'category': 'Computers and Laptops', 
      'products': ['TechPro Ultrabook', 'BlueWave Gaming Laptop', 
           'PowerLite Convertible', 
      'TechPro Desktop', 'BlueWave Chromebook']}]
    """

    few_shot_user_3 = """What smartphones do you have?"""
    few_shot_assistant_3 = """ 
    [{'category': 'Smartphones and Accessories', 
      'products': ['SmartX ProPhone', 'MobiTech PowerCase', 
                    'SmartX MiniPhone']}]
    """
    
    messages =  [  
    {'role':'system', 
        'content': system_message},    
    {'role':'user', 
        'content': f"{delimiter}{few_shot_user_1}{delimiter}"},  
    {'role':'assistant', 
        'content': few_shot_assistant_1},
    {'role':'user', 
        'content': f"{delimiter}{few_shot_user_2}{delimiter}"},  
    {'role':'assistant', 
        'content': few_shot_assistant_2}, 
    {'role':'user', 
        'content': f"{delimiter}{few_shot_user_3}{delimiter}"},  
    {'role':'assistant', 
        'content': few_shot_assistant_3}, 
    {'role':'user', 
        'content': f"{delimiter}{user_input}{delimiter}"}
    ]

    return get_completion(messages)


def eval_response_with_ideal(response, ideal, debug=False):
    # json.loads() expects double quotes, not single quotes
    json_like_str = response.replace("'", '"')

    try:
        # Parse into a list of dictionaries
        l_of_d = json.loads(json_like_str)
    except json.JSONDecodeError as e:
        if debug:
            print(f"Error parsing JSON: {e}")
        return 0.0

    # Print response and ideal once when debug is enabled
    if debug:
        print(f'Response:\n{l_of_d}')
        print(f'Ideal answer:\n{ideal}')

    # Special case: both response and ideal are empty lists
    if not l_of_d and not ideal:
        if debug:
            print("Correct. Response matches the ideal answer.")
        return 1.0

    # Case when either response or ideal is empty
    if not l_of_d or not ideal:
        if debug:
            print("Incorrect. One of response or ideal answer is empty while the other is not.")
        return 0.0

    correct = 0.0

    for d in l_of_d:
        cat = d.get('category')
        prod_l = d.get('products')

        if cat and prod_l:
            # Convert list to set for comparison
            prod_set = set(prod_l)
            ideal_cat = ideal.get(cat)

            if not ideal_cat:
                if debug:
                    print(f"Did not find category '{cat}' in ideal.")
                continue

            prod_set_ideal = set(ideal_cat)

            # Debug output for correctness check
            # if debug:
                # print(f"Response product set: {prod_set}")
                # print(f"Ideal product set: {prod_set_ideal}")

            if prod_set == prod_set_ideal:
                correct += 1
                if debug:
                    print(f'Category: {cat}')
                    print("Correct. Response matches the ideal answer.")
            else:
                if debug:
                    print("Incorrect.")
                    if prod_set < prod_set_ideal:
                        print("Response is a subset of the ideal answer.")
                    elif prod_set > prod_set_ideal:
                        print("Response is a superset of the ideal answer.")
        else:
            if debug:
                print(f"Missing category or products in response: {d}")

    # Calculate the percentage of correct matches
    pc_correct = correct / len(l_of_d) if l_of_d else 0

    return pc_correct


def get_products():
    return products


def get_products_and_category():
    """
    Used in L5
    """
    products = get_products()
    products_by_category = defaultdict(list)
    for product_name, product_info in products.items():
        category = product_info.get('category')
        if category:
            products_by_category[category].append(product_info.get('name'))
    
    return dict(products_by_category)


def evaluate_all_pair_set(msg_ideal_pairs_set):
    # Note, this will not work if any of the api calls time out
    products_and_category = get_products_and_category()
    score_accum = 0
    for i, pair in enumerate(msg_ideal_pairs_set):
        print(f'Example {i}:')
        
        customer_msg = pair['customer_msg']
        ideal = pair['ideal_answer']
        response = find_category_and_product_v3(customer_msg, products_and_category)

        print(f'Customer message: {customer_msg}')
        #print(f'Response: {response}')
        #print(f'Ideal answer: {ideal}')

        score = eval_response_with_ideal(response,ideal,debug=True)
        print(f'Score: {score}\n')
        score_accum += score   

    n_examples = len(msg_ideal_pairs_set)
    fraction_correct = score_accum / n_examples
    print(f'Fraction correct out of {n_examples}: {fraction_correct}')


# product look up (either by category or by product within category)
def get_product_by_name(name):
    products = get_products()
    return products.get(name, None)


def get_products_by_category(category):
    products = get_products()
    return [product for product in products.values() if product['category'] == category]


def get_products_from_query(user_msg):
    """
    Code from L5, used in L8
    """
    products_and_category = get_products_and_category()
    system_message = f"""
    You will be provided with customer service queries. \
    The customer service query will be delimited with {delimiter} characters.
    Output a python list of json objects, where each object has the following format:
        'category': <one of Computers and Laptops, Smartphones and Accessories, Televisions and Home Theater Systems, \
    Gaming Consoles and Accessories, Audio Equipment, Cameras and Camcorders>,
    OR
        'products': <a list of products that must be found in the allowed products below>

    Where the categories and products must be found in the customer service query.
    If a product is mentioned, it must be associated with the correct category in the allowed products list below.
    If no products or categories are found, output an empty list.

    The allowed products are provided in JSON format.
    The keys of each item represent the category.
    The values of each item is a list of products that are within that category.
    Allowed products: {products_and_category}
    """
    
    messages =  [  
    {'role':'system','content': system_message},    
    {'role':'user','content': f"{delimiter}{user_msg}{delimiter}"}
    ] 

    category_and_product_response = get_completion(messages)
    
    # Debug print to check raw response
    # print(f"Raw response from get_completion: {category_and_product_response}")

    # Strip any extra delimiters or unwanted text such as ```python
    if category_and_product_response.startswith('```python'):
        category_and_product_response = category_and_product_response[9:]  # Remove '```python'
    if category_and_product_response.endswith('```'):
        category_and_product_response = category_and_product_response[:-3]  # Remove closing '```'

    # Clean and ensure the output is valid JSON (replace single quotes and fix potential format issues)
    cleaned_response = category_and_product_response.replace("'", '"')

    try:
        json_response = json.loads(cleaned_response)
        return json_response
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON. Raw response: {cleaned_response}")
        print(f"Exception: {e}")
        return []
    
    
def get_mentioned_product_info(data_list):
    """
    Used in L5 and L6
    """
    product_info_l = []

    if data_list is None:
        return product_info_l

    for data in data_list:
        try:
            if "products" in data:
                products_list = data["products"]
                for product_name in products_list:
                    product = get_product_by_name(product_name)
                    if product:
                        product_info_l.append(product)
                    else:
                        print(f"Error: Product '{product_name}' not found")
            elif "category" in data:
                category_name = data["category"]
                category_products = get_products_by_category(category_name)
                for product in category_products:
                    product_info_l.append(product)
            else:
                print("Error: Invalid object format")
        except Exception as e:
            print(f"Error: {e}")

    return product_info_l


def answer_user_msg(user_msg,product_info):
    """
    Code from L5, used in L6
    """
    system_message = f"""
    You are a customer service assistant for a large electronic store. \
    Respond in a friendly and helpful tone, with concise answers. \
    Make sure to ask the user relevant follow up questions.
    """
    # user_msg = f"""
    # tell me about the smartx pro phone and the fotosnap camera, the dslr one. Also what tell me about your tvs"""
    messages =  [  
    {'role':'system', 'content': system_message},   
    {'role':'user', 'content': f"{delimiter}{user_msg}{delimiter}"},  
    {'role':'assistant', 'content': f"Relevant product information:\n{product_info}"}
    ] 
    response = get_completion(messages)
    return response


# Evaluate with rubric  
def eval_with_rubric(test_set, assistant_answer):
    cust_msg = test_set['customer_msg']
    context = test_set['context']
    completion = assistant_answer
    
    system_message = """\
    You are an assistant that evaluates how well the customer service agent \
    answers a user question by looking at the context that the customer service \
    agent is using to generate its response. 
    """

    user_message = f"""\
    You are evaluating a submitted answer to a question based on the context \
    that the agent uses to answer the question.
    Here is the data:
        [BEGIN DATA]
        ************
        [Question]: {cust_msg}
        ************
        [Context]: {context}
        ************
        [Submission]: {completion}
        ************
        [END DATA]

    Compare the factual content of the submitted answer with the context. \
    Ignore any differences in style, grammar, or punctuation.
    Answer the following questions:
        - Is the Assistant response based only on the context provided? (Y or N)
        - Does the answer include information that is not provided in the context? (Y or N)
        - Is there any disagreement between the response and the context? (Y or N)
        - Count how many questions the user asked. (output a number)
        - For each question that the user asked, is there a corresponding answer to it?
        Question 1: (Y or N)
        Question 2: (Y or N)
        ...
        Question N: (Y or N)
        - Of the number of questions asked, how many of these questions were addressed by the answer? (output a number)
    """

    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]

    response = get_completion(messages)
    return response

def eval_vs_ideal(test_set, assistant_answer):
    cust_msg = test_set['customer_msg']
    ideal = test_set['ideal_answer']
    completion = assistant_answer
    
    system_message = """\
    You are an assistant that evaluates how well the customer service agent \
    answers a user question by comparing the response to the ideal (expert) response
    Output a single letter and nothing else. 
    """

    user_message = f"""\
    You are comparing a submitted answer to an expert answer on a given question. Here is the data:
    [BEGIN DATA]
    ************
    [Question]: {cust_msg}
    ************
    [Expert]: {ideal}
    ************
    [Submission]: {completion}
    ************
    [END DATA]

    Compare the factual content of the submitted answer with the expert answer. Ignore any differences in style, grammar, or punctuation.
    The submitted answer may either be a subset or superset of the expert answer, or it may conflict with it. Determine which case applies. 
    Answer the question by selecting one of the following options, and make sure to print out the option letter and the whole statement every time:
    (A) The submitted answer is a subset of the expert answer and is fully consistent with it.
    (B) The submitted answer is a superset of the expert answer and is fully consistent with it.
    (C) The submitted answer contains all the same details as the expert answer.
    (D) There is a disagreement between the submitted answer and the expert answer.
    (E) The answers differ, but these differences don't matter from the perspective of factuality.
"""

    messages = [
        {'role': 'system', 'content': system_message},
        {'role': 'user', 'content': user_message}
    ]

    response = get_completion(messages)
    return response
