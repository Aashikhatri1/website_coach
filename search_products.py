import os
import openai
from dotenv import load_dotenv
import time
from tinydb import TinyDB, Query
import json

# Load environment variables
load_dotenv()
# from fetchData import fetchDataFromDatabase

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
    start_time = time.time()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key is None:
        raise ValueError("The OPENAI_API_KEY is not set in the environment.")

    if userQuestion.lower() == "exit":
        return "Thank You"

    history = get_session_history(session_id)
    print('history: ', history)

    model = "gpt-3.5-turbo"


    # Format the prompt as a conversation, if necessary
    conversation = [
        {
            "role": "system",
            "content": """Hi, If I ask you question regarding any product, then create a filter in this format and set isFilter property  as 'True' and if I ask you general questions and filters are not being generated, then set isFilter perperty as 'False' then do not create filter : 
            {{
                "data": "Answer to normal query and general question answers."
                "isFilter":true,
                "filterData": {{ 
                    "product": "category of the product, eg. car perfume, laptop etc",
                    "budget": "Array which contain minimum and maximum budget in number. minimum should be 0 unless and until query doesn't specify the minimum amount",
                    "brand": "Name of the brand such as Apple, Samsung etc",
                    }}
            }}
            If any filter is not applicable, remove it from json. Show only the output json.""",
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
            api_key=openai_api_key,
        )
        # Extract the answer from the response
        answer = response.choices[0].message.content.strip()
    except openai.error.InvalidRequestError as e:
        print("Invalid Request Error:", e)
        return "OpenAI request error"

    print("Received answer from OpenAI:", answer)
    end_time_gpt = time.time()

    final_response = None
    filter_data = {} 
    # Convert the string answer to a JSON object if it is JSON-formatted
    try:
        # Remove any unwanted newlines and backslashes from the string
        answer = answer.replace("\n", "").replace("\\", "")
        # Attempt to convert the string to a JSON object
        answer_json = json.loads(answer)
        print('answer_json: ', answer_json)

        print(answer)
        if isinstance(answer_json, dict) and answer_json.get("isFilter"):
            print("step 1")
            # Directly access 'filterData' from answer_json, not from answer_json["data"]
            filter_data = answer_json.get("filterData", {})
            # print(filter_data)
           
        else:
            print("Not found")
    except json.JSONDecodeError:
        # If an error occurs, the answer is not JSON-formatted, so return as is
        answer_json = answer
    
    # Update the session history
    conversation_history = conversation[1:]  # Exclude the system message
    save_session_history(session_id, conversation_history)

    return filter_data

def create_url(filter_data):
    product_links = []
    base_url = "http://amazon.com/search-result?"

    if "product" in filter_data or "brand" in filter_data:
        query_params = []

        if "product" in filter_data:
            product = filter_data["product"]
            query_params.append(f"title={product.replace(' ', '-')}")
        
        if "brand" in filter_data:
            brand = filter_data["brand"]
            query_params.append(f"brand={brand.replace(' ', '-')}")
        
        formatted_string = base_url + "&".join(query_params)
        product_links.append(formatted_string)

    return {"product_links": product_links}


if __name__ == "__main__":
    session_id = "1234abcd134"
    # chatResponse = text_to_text_conversation(session_id, "I am looking for a 3BHK flat in Sushant Lok 3 under 4 crores")
    filter_data = text_to_text_conversation(session_id, "I want an samsng laptop")
    print(filter_data)
    product_links = create_url(filter_data)
    print(product_links)


