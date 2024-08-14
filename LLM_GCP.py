from fastapi import FastAPI, HTTPException
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from google.cloud import storage
import pandas as pd
import datetime
import os
import logging
from dotenv import load_dotenv
import tiktoken  # Tokenizer library

# Load environment variables
load_dotenv()
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

# Initialize Google Cloud Storage client
storage_client = storage.Client.from_service_account_json("key.json")

# Initialize the FastAPI app
app = FastAPI(
    title="Langchain Server",
    version="1.0",
    description="A simple API Server"
)

# Initialize the model with a cheaper model ID
model_name = "gpt-4o-mini"
model_FAQ = ChatOpenAI(model=model_name)
base_prompt_FAQ = ChatPromptTemplate.from_template(
    "You are an expert for {text} patients. "
    "Provide exactly {num_faqs} FAQs in the 1st column, 2:answers, 3:source, and 4:keyword in a tabular format. "
    "Do not include the number before questions. Continue from these last questions given in the previous prompt: {last_two_questions}. "
    "Ensure the total number of FAQs provided is exactly {num_faqs}."
)


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def store_data_to_gcs(faq_df, disease):
    bucket_name = "project1-app"  # Replace with your GCS bucket name
    file_name = f"{disease}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"

    # Convert DataFrame to CSV
    csv_data = faq_df.to_csv(index=False)

    # Create a blob and upload the CSV data
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    blob.upload_from_string(csv_data, content_type='csv')

    # Generate a signed URL for the blob
    signed_url = blob.generate_signed_url(version="v4", expiration=datetime.timedelta(hours=1), method="GET")

    logger.info(f"File uploaded successfully. You can access it here: {signed_url}")

    return signed_url

def transform_data(response, disease, seen_questions):
    faq_response = response.content
    # Parsing the response to extract FAQ data
    faq_lines = faq_response.split("\n")
    faq_data = []
    for line in faq_lines:
        if line.startswith('|') and not line.startswith('| **FAQ**'):
            faq_row = line.strip('|').split('|')
            question = faq_row[0].strip()
            if question not in seen_questions:
                seen_questions.append(question)
                faq_data.append([question, faq_row[1].strip(), faq_row[2].strip(), faq_row[3].strip()])
    # Creating a DataFrame from the parsed FAQ data
    faq_df = pd.DataFrame(faq_data, columns=["FAQ", "Answer", "Source", "Keyword"])

    # Ensure disease name is present in the "Keyword" column
    faq_df['Keyword'] = faq_df['Keyword'].apply(lambda x: f"{x} {disease}" if disease.lower() not in x.lower() else x)

    return faq_df

def count_tokens(text, model_name):
    enc = tiktoken.encoding_for_model(model_name)
    tokens = enc.encode(text)
    return len(tokens)

def get_response(disease, num_faqs=500):
    accumulated_data = []
    seen_questions = []
    chunk_size = 200  # Adjust this size based on API capacity
    total_faqs = 0
    total_tokens = 0

    while total_faqs < num_faqs:
        try:
            # Format the prompt with the last two seen questions
            last_two_questions = seen_questions[-2:]
            prompt_text = base_prompt_FAQ.format(text=disease, num_faqs=chunk_size, last_two_questions=last_two_questions)
            # Get the response from the model
            response = model_FAQ([HumanMessage(content=prompt_text)])
            faq_df = transform_data(response, disease, seen_questions)

            accumulated_data.append(faq_df)
            total_faqs += len(faq_df)

            # Count tokens
            tokens = count_tokens(response.content, model_name)
            total_tokens += tokens

            logger.info(f"Accumulated FAQs: {total_faqs}, Tokens generated in this step: {tokens}, Total tokens so far: {total_tokens}")

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    final_faq_df = pd.concat(accumulated_data).head(num_faqs)
    file_link = store_data_to_gcs(final_faq_df, disease)
    return file_link

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/{disease}")
def read_disease(disease: str):
    response = get_response(disease)
    return response

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
