#!/usr/bin/env python
# coding: utf-8

# In[21]:


# Use Pandas to transform the data into the desired format.
import pandas as pd
import json
from sklearn.model_selection import train_test_split

n=2000

# Load data from the Excel file
df = pd.read_excel('Medicine_description.xlsx', sheet_name='Sheet1', header=0, nrows=n)

# Get unique values in the 'Reason' column and assign numerical indices
reasons = df["Reason"].unique()
reasons_dict = {reason: i for i, reason in enumerate(reasons)}

# Add the formatted content to the 'Drug_Name' column
df["Drug_Name"] = "Drug: " + df["Drug_Name"] + "\n" + "Malady:"

# Replace 'Reason' with the mapped numerical value (classification target)
df["Reason"] = df["Reason"].apply(lambda x: "" + str(reasons_dict[x]))

# Drop the 'Description' column
df.drop(["Description"], axis=1, inplace=True)

# Split the data into training and validation datasets (80% train, 20% validate)
train_df, val_df = train_test_split(df, test_size=0.2, random_state=42)

# Function to convert a DataFrame into JSONL format
def convert_to_jsonl(df, output_file):
    output = []
    system_message = {"role": "system", "content": "You are a drug classification assistant."}
    
    for _, row in df.iterrows():
        user_message = {"role": "user", "content": row["Drug_Name"]}
        assistant_message = {"role": "assistant", "content": row["Reason"]}
        output.append({"messages": [system_message, user_message, assistant_message]})
    
    with open(output_file, "w") as f:
        for entry in output:
            f.write(json.dumps(entry) + "\n")

# Convert training and validation DataFrames to JSONL files
convert_to_jsonl(train_df, "train_data.jsonl")
convert_to_jsonl(val_df, "val_data.jsonl")


# In[16]:


import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# In[23]:


# Upload the training and validation files
train_data = client.files.create(
  file=open("train_data.jsonl", "rb"),
  purpose="fine-tune")

val_data = client.files.create(
  file=open("val_data.jsonl", "rb"),
  purpose="fine-tune")


# In[26]:


# Create a fine-tuned model
fine_tune_job = client.fine_tuning.jobs.create(
  training_file=train_data.id,
  model="gpt-4o-mini-2024-07-18",
  validation_file=val_data.id,
  suffix="drug-classifier"
)


# In[28]:


# Print the fine-tuning job details
print(f"Fine-tuning job created with ID: {fine_tune_job.id}")
updated_job = client.fine_tuning.jobs.retrieve(fine_tune_job.id)
print(f"Fine-tuned Model ID: {updated_job.fine_tuned_model}")


# In[30]:


# Retrieve the state of a fine-tune
updated_job


# In[63]:


# Use the fine-tuned model
drugs = [
    "A CN Gel(Topical) 20gmA CN Soap 75gm",  # Class 0
    "Addnok Tablet 20'S",                    # Class 1
    "ABICET M Tablet 10's",                  # Class 2
]

for drug_name in drugs:
    prompt = "Drug: {}\nMalady:".format(drug_name)
    completion = client.chat.completions.create(
      model=updated_job.fine_tuned_model,
      messages=[
        {"role": "user", "content": prompt}
      ])
    print(completion.choices[0].message.content)


# In[59]:


# Let's use a drug from each class
drugs = [
    "What is 'A CN Gel(Topical) 20gmA CN Soap 75gm' used for?",  # Class 0
    "What is 'Addnok Tablet 20'S' used for?",  # Class 1
    "What is 'ABICET M Tablet 10's' used for?",  # Class 2
]

class_map = {
    0: "Acne",
    1: "Adhd",
    2: "Allergies",
}

# Returns a drug class for each drug
for drug in drugs:
    drug_name = drug.split("'")[1] 
    prompt = "Drug: {}\nMalady:".format(drug)
    completion = client.chat.completions.create(
      model=updated_job.fine_tuned_model,
      messages=[
        {"role": "user", "content": prompt}
      ])
    response = completion.choices[0].message.content
    
    try:
        print(drug_name + " is used for " + class_map[int(response)] + ".")
    except:
        print("I don't know what " + drug_name + " is used for.")
    print()


# In[ ]:




