from flask import Flask, request, jsonify
import search_products_pplx  # Import your existing code here
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/process_request', methods=['POST'])
def process_request():
    # Extract data from the request
    data = request.json
    session_id = data.get('session_id')
    user_question = data.get('user_question')

    # Process the request using your existing functions
    filter_data = search_products_pplx.text_to_text_conversation(session_id, user_question)
    product_links = search_products_pplx.create_url(filter_data)

    # Return the response
    # return jsonify(product_links)
    return product_links

if __name__ == '__main__':
    app.run(debug=True)
