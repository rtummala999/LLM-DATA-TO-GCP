LLM-DATA-TO-GCP


# Langchain Server

## Overview

API for generating FAQs about medical diseases using the OpenAI GPT model. The server interacts with Google Cloud Storage to store generated FAQ data and provides a RESTful API to access the information.

## Features

- **FastAPI**: Web framework for building APIs.
- **Langchain**: For interacting with GPT models.
- **Google Cloud Storage**: For storing generated FAQ data.
- **Logging**: For tracking the process and debugging.
- **Environment Variables**: Loaded using `dotenv`.

## Requirements

- Python 3.8+
- Google Cloud SDK
- `pip install -r requirements.txt`

## Setup

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/langchain-server.git
    cd langchain-server
    ```

2. **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3. **Set up environment variables:**

    Create a `.env` file in the root directory of the project and add your OpenAI API key:

    ```dotenv
    OPENAI_API_KEY=your_openai_api_key
    ```

    Ensure you have the `key.json` file for Google Cloud Storage access.

4. **Run the application:**

    ```bash
    uvicorn main:app --host 127.0.0.1 --port 8001
    ```

## API Endpoints

- **GET `/`**: Returns a simple "Hello World" message.

- **GET `/{disease}`**: Generates and returns a URL to the CSV file containing FAQs for the specified disease.

## Code Description

- **`main.py`**: Contains the FastAPI application, API endpoints, and logic for interacting with the GPT model and Google Cloud Storage.
- **`store_data_to_gcs`**: Uploads the generated FAQ CSV file to Google Cloud Storage and returns a signed URL.
- **`transform_data`**: Parses the FAQ response from the GPT model and formats it into a DataFrame.
- **`count_tokens`**: Counts the number of tokens in the response content.
- **`get_response`**: Handles the process of generating FAQs, including making multiple requests to the GPT model as needed.

## Logging

The application uses Python's built-in logging module to log information about the FAQ generation process.



## Contact

For questions or feedback, please contact tummalaramgopal@gmail.com 
