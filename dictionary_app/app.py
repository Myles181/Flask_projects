from flask import Flask, render_template, url_for, redirect, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env")
password = os.getenv("PASSWORD")
secret_key = os.getenv("SECRET_KEY")
words_api_key = os.getenv("API_KEY")

# Configuration for app
app = Flask(__name__)
app.config["SECRET_KEY"] = secret_key
app.config["MONGO_URI"] = f"mongodb+srv://cyrile450:{password}@dictionary.dxa2nfr.mongodb.net/?retryWrites=true&w=majority"

# Connect to dictionary MongoDB database
mongo = MongoClient(app.config["MONGO_URI"])
db = mongo["authenticatorDB"]

# Use bcrypt for password hashing
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/')
def hello_world():
    logging.debug("Hello World route accessed.")
    return "<h1>Hello World!</h1>"

@app.route('/login')
def login():
    logging.debug("Login route accessed.")
    return render_template('login.html', text="")

@app.route('/login', methods=['POST', 'GET'])
def authenticate():
    logging.debug("Authentication attempt.")
    email = request.form.get('email')
    password = request.form.get('password')
    user_collection = db["users"]
    user = user_collection.find_one({"email": email})
    recent_words = ["Apple", "Puppy", "Microbe"]

    if user and bcrypt.check_password_hash(user['password'], password):
        logging.debug("Authentication successful.")
        # return render_template('profile.html', username=user['username'], user_id=user['_id'], recent=recent_words)
        return redirect(url_for('/result/success'))
    else:
        logging.debug("Authentication failed.")
        # return render_template('login.html', text="Incorrect email or password")
        return redirect(url_for('/result/failed'))

@app.route('/signup')
def signup():
    logging.debug("Signup route accessed.")
    return render_template('signup.html')

@app.route('/test', methods=['POST', 'GET'])
def test():
    logging.debug("Test route accessed.")
    item = request.args.get("item")
    return jsonify({"Success": item})

@app.route('/register', methods=['POST', 'GET'])
def register():
    logging.debug("Registration attempt.")
    username = request.args.get('username')
    email = request.args.get('email')
    password = request.args.get('password')

    logging.debug(f"Received registration data - Username: {username}, Email: {email}")

    # Uncomment the following line to debug the password
    # print(password)

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    user_collection = db["users"]

    # Check if the email is already registered
    if user_collection.find_one({"email": email, "username": username}) is True:
        logging.debug("Email already registered.")
        # return render_template(url_for('login'), text="Email already registered")
        return redirect(url_for('result/failed'))

    # Insert the user document
    user_collection.insert_one({'username': username, 'email': email, 'password': hashed_password})
    logging.debug("Registration successful.")
    return redirect(url_for('/result/success'))

@app.route('/result/<re>', methods=['GET'])
def result(re):
    return re

@app.route('/words', methods=['POST', 'GET'])
def get_request():
    logging.debug("Word search request.")
    word_searched = request.json.get('word')

    if not word_searched:
        logging.debug("Word not provided in the JSON data.")
        return "Word not provided in the JSON data."

    api_url = f'https://wordsapiv1.p.mashape.com/words/{word_searched}'
    headers = {
        'X-Mashape-Key': words_api_key,
        'Accept': 'application/json'
    }

    response = requests.get(api_url, headers=headers)

    if response.status_code == 200:
        logging.debug("Word search successful.")
        return jsonify(response.json())
    else:
        logging.debug(f"Error {response.status_code}: {response.text}")
        return f"Error {response.status_code}: {response.text}"

if __name__ == "__main__":
    app.run(debug=True)
