from flask import Flask, render_template, url_for, redirect, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import os
import logging
from dotenv import load_dotenv
from bson import ObjectId
from colorama import Fore

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
    logging.debug(Fore.GREEN + "Hello World route accessed.")
    return render_template('index.html')


@app.route('/result/<re>', methods=['GET'])
def result(re):
    """ Result route
    """
    return re


@app.route('/login')
def login():
    logging.debug(Fore.GREEN + "Login route accessed.")
    return render_template('login.html', text="")

@app.route('/login', methods=['POST', 'GET'])
def authorize():
    """ Authorize/Login User
    """
    logging.debug(Fore.GREEN + "Authentication attempt.")

    # Get login data
    """ email = request.form.get('email')
        password = request.form.get('password')
        """
    email = request.args.get('email')
    password = request.args.get('password')

    # Get users collection
    user_collection = db["users"]
    # Find user through email
    user = user_collection.find_one({"email": email})
    if user is None:
        logging.debug(Fore.GREEN + f'User does not exist. Check your usernname')
        return redirect(url_for('return', re='failed'))

    # recent_words = ["Apple", "Puppy", "Microbe"]

    # If user is True and user password is equal password gotten. Else auth fail
    if user and bcrypt.check_password_hash(user['password'], password):
        ID = user['_id']
        logging.debug(Fore.GREEN + f"Authentication successful.\nUser_ID: {ID}")
        # return render_template('profile.html', username=user['username'], user_id=user['_id'], recent=recent_words)
        return redirect(url_for('result', re='success'))
    else:
        logging.debug(Fore.GREEN + "Authentication failed. Check username and password.")
        # return render_template('login.html', text="Incorrect email or password")
        return redirect(url_for('result', re='failed'))

@app.route('/signup')
def signup():
    """ Signup view
    """
    logging.debug(Fore.GREEN + "Signup route accessed.")
    return render_template('signup.html')

@app.route('/register', methods=['POST', 'GET'])
def register():
    """ Register New User
    """

    # Check is method of request is POST
    if request.method != 'POST':
        method = request.method
        logging.debug(Fore.GREEN + f'Send a post request. Request sent: {method}')
        return redirect(url_for('result', re='failed'))

    logging.debug(Fore.GREEN + "Registration attempt.")
    # Get signip data
    """ username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
    """
    username = request.args.get('username')
    email = request.args.get('email')
    password = request.args.get('password')

    # Log if user date is not None
    logging.debug(Fore.GREEN + f"Received registration data - Username: {username}, Email: {email}, Password: {password}")

    # Uncomment the following line to debug the password
    # print(password)

    #Hash password in 64-bit encoding
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    #Get users collection
    user_collection = db["users"]

    # CHeck i fuser name exists
    if user_collection.find_one({"username": username}) is None:
        # Check if the email is already registered
        if user_collection.find_one({"email": email}):
            logging.debug(Fore.GREEN + "User already has an account")
            # return render_template(url_for('login'), text="Email already registered")
            return redirect(url_for('result', re='failed'))
        else:
            # If user doesn't have an account already. Insert the user document
            user_collection.insert_one({'username': username, 'email': email, 'password': hashed_password})
            logging.debug(Fore.GREEN + "Registration successful.")
            return redirect(url_for('result', re='success'))

    else:
        logging.debug(Fore.GREEN + "Pick another username. Username already exists")
        return redirect(url_for('result', re="Failed"))


@app.route('/delete_user/<user_id>', methods=['GET'])
def delete_user(user_id):
    logging.debug(Fore.GREEN + f"Delete user request for user ID: {user_id}")
    user_collection = db["users"]

    # Check if the user with the given ID exists
    user = user_collection.find_one({"_id": ObjectId(user_id)})

    if user:
        # Delete the user
        user_collection.delete_one({"_id": ObjectId(user_id)})
        logging.debug(Fore.GREEN + "User deleted successfully.")
        return redirect(url_for('result', re='User deleted successfully'))
    else:
        logging.debug(Fore.GREEN + "User not found.")
        return redirect(url_for('result', re='User not found'))

@app.route('/update_profile/<user_id>', methods=['POST', 'GET'])
def update_profile(user_id):
    """Update profile
    """
    logging.debug(Fore.GREEN + f"Update profile request for user ID: {user_id}")
    user_collection = db["users"]

    # Check if the user with the given ID exists
    user = user_collection.find_one({"_id": ObjectId(user_id)})

    if user:
        if request.method == 'POST':
            # Update user profile information
            """
                new_username = request.form.get('new_username')
                new_email = request.form.get('new_email')
                new_password = request.form.get('new_password')
                """
            new_username = request.args.get('new_username')
            new_email = request.args.get('new_email')
            new_password = request.args.get('new_password')


            # Validate and update the fields as needed
            if new_username:
                user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"username": new_username}})
            if new_email:
                user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"email": new_email}})
            if new_password:
                hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
                user_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"password": hashed_password}})

            logging.debug(Fore.GREEN + "User profile updated successfully.")
            return redirect(url_for('result', re='User profile updated successfully'))
        else:
            return render_template('update_profile.html', user=user)
    else:
        logging.debug(Fore.GREEN + "User not found.")
        return redirect(url_for('result', re='User not found'))


@app.route('/test', methods=['POST', 'GET'])
def test():
    """ Just a test route
    """
    logging.debug(Fore.GREEN + "Test route accessed.")
    item = request.args.get("item")
    return jsonify({"Success": item})


@app.route('/words', methods=['POST', 'GET'])
def get_word():
    """ Dictionary query function
    """
    
    logging.debug(Fore.GREEN + "Word search request.")
    
    # Get the word
    word_searched = request.json.get('word')

    # Check if the word is empty
    if not word_searched:
        logging.debug(Fore.GREEN + "Word not provided in the JSON data.")
        return jsonify({'error': 'Word not provided in the JSON data'})

    api_url = f'https://api.dictionaryapi.dev/api/v2/entries/en/{word_searched}'
    
    response = requests.get(api_url)

    # If Successful return the response. Else return an error
    if response.status_code == 200:
        data = response.json()
        if data and isinstance(data, list) and len(data) > 0:
            # Extract meaning and synonyms from the response
            word_data = data[0]
            meaning = word_data.get('meanings', [])[0].get('definitions', [])[0].get('definition', '')
            synonyms = word_data.get('meanings', [])[0].get('definitions', [])[0].get('synonyms', [])

            logging.debug(Fore.GREEN + "Word search successful.")
            return jsonify({
                'status_code': 200,
                'meaning': meaning,
                'synonyms': synonyms
            })
        else:
            logging.debug(Fore.GREEN + "No data found for the word.")
            return jsonify({'error': 'No data found for the word'})
    else:
        logging.debug(Fore.GREEN + f"Error {response.status_code}: {response.text}")
        return jsonify({'error': f"Error {response.status_code}: {response.text}"})


if __name__ == "__main__":
    app.run(debug=True)
