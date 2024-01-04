import os
import openai
from dotenv import load_dotenv
import time
from tinydb import TinyDB, Query
import json

# Load environment variables
load_dotenv()
# from fetchData import fetchDataFromDatabase
PPLX_API_KEY = os.environ.get("PPLX_API_KEY")
model = "llama-2-70b-chat"
# Initialize TinyDB
session_db = TinyDB('session_db.json')
session_table = session_db.table('sessions')

def get_session_history(session_id):
    """ Retrieve session history from the database. """
    Session = Query()
    result = session_table.search(Session.session_id == session_id)
    if result:
        return result[0]['history']
    return []

def save_session_history(session_id, history):
    """ Save session history to the database. """
    Session = Query()
    if session_table.search(Session.session_id == session_id):
        session_table.update({'history': history}, Session.session_id == session_id)
    else:
        session_table.insert({'session_id': session_id, 'history': history})

def text_to_text_conversation(session_id, userQuestion):
    message = None
    start_time = time.time()
    
    if userQuestion.lower() == "exit":
        return "Thank You"

    history = get_session_history(session_id)
    print('history: ', history)

    # Format the prompt as a conversation, if necessary
    conversation = [
        {
            "role": "system",
            "content": """"This is a system designed to assist with e-commerce website queries. When asked about products, "
                "the system should create a filter in a specific JSON format with 'isFilter' set to 'True'. If the question is general "
                "and does not require a filter, set 'isFilter' to 'False'. Do not assume any information that is not explicitly provided. "
                "Create a filter even when there is only single information such as if only product category is given."
                "The JSON format for responses is as follows:\n" 
            {{
                "data": "Answer to normal query and general question answers."
                "message": "Sure, Here are the options based on your query"
                "isFilter":true,
                "filterData": {{ 
                    "product": "category of the product, eg. car perfume, laptop, stationary, home decor etc",
                    "budget": "Array which contain minimum and maximum budget in number. minimum should be 0 unless and until query doesn't specify the minimum amount",
                    "brand": "Name of the brand such as Apple, Samsung etc",
                    }}
            }}
            If any filter is not applicable, remove it from json. Show only the output json.
            Omit all the filters for which information is not given.""",
        },
        
    ]

    # Add history messages if they exist
    if history:
        conversation.extend(history)

    # Add the current user message
    conversation.append({"role": "user", "content": userQuestion})

    # Check and print conversation for debugging
    for msg in conversation:
        if not msg.get('content'):
            print("Error: Message content is empty or invalid")
            return "Message content error"
        print(f"Role: {msg['role']}, Content: {msg['content']}")

    try:
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model=model,
            messages=conversation,
            api_base="https://api.perplexity.ai",
            api_key=PPLX_API_KEY, 
        )
        # Extract the answer from the response
        answer = response.choices[0].message.content.strip()
    except openai.error.InvalidRequestError as e:
        print("Invalid Request Error:", e)
        return "OpenAI request error"

    print("Received answer from OpenAI:", answer)
    
    filter_data = {} 
    # Convert the string answer to a JSON object if it is JSON-formatted
    try:
        # Find the start of the JSON object
        json_start = answer.find('{')
        # Find the end of the JSON object
        json_end = answer.rfind('}') + 1
        # Extract the JSON part from the answer
        json_answer = answer[json_start:json_end]
        # Convert to a JSON object
        answer_json = json.loads(json_answer)
        print('answer_json: ', answer_json)

        if answer_json.get("isFilter"):
            filter_data = answer_json.get("filterData", {})
            message = answer_json.get("message", "")
        else:
            filter_data = {}
            message = answer_json.get("data", "")

    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        filter_data = {}
        message = answer

    # Update the session history
    conversation_history = conversation[1:]  # Exclude the system message
    save_session_history(session_id, conversation_history)

    return filter_data, message

def create_url(filter_data, message):
    product_links = []
    
    base_url = "https://ecom-app-orcin.vercel.app/search-result?"

    # Check if 'product' or 'brand' keys have non-empty values
    if filter_data.get("product") or filter_data.get("brand"):
        query_params = []

        # Check if 'product' key is present and has a non-empty value
        if filter_data.get("product"):
            product = filter_data["product"]
            if product.strip():  # Check if the product value is not just empty spaces
                query_params.append(f"title={product.replace(' ', '-')}")

        # Check if 'brand' key is present and has a non-empty value
        if filter_data.get("brand"):
            brand = filter_data["brand"]
            if brand.strip():  # Check if the brand value is not just empty spaces
                query_params.append(f"brand={brand.replace(' ', '-')}")
        
        # Construct the URL only if there are query parameters
        if query_params:
            formatted_string = base_url + "&".join(query_params)
            product_links.append(formatted_string)

    return {"message": message, "link": product_links}


# if __name__ == "__main__":
#     session_id = "1234abcd1347xyz12347"
    
#     filter_data, message = text_to_text_conversation(session_id, "I want Home decor products")
#     print(filter_data)
#     product_links = create_url(filter_data, message)
#     print(product_links)


