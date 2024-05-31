from flask import Flask, request, jsonify, redirect
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK_URL = 'https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN'

@app.route('/')
def home():
    return "Welcome to the registration and KYC page."

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return '''
            <form action="/register" method="post">
                Email: <input type="email" name="email"><br>
                Password: <input type="password" name="password"><br>
                <input type="submit" value="Register">
            </form>
        '''
    else:
        email = request.form['email']
        password = request.form['password']
        # Save the user details to the database
        return redirect('/kyc')

@app.route('/kyc', methods=['GET', 'POST'])
def kyc():
    if request.method == 'GET':
        return '''
            <form action="/kyc" method="post" enctype="multipart/form-data">
                Country: <input type="text" name="country"><br>
                First Name: <input type="text" name="first_name"><br>
                Last Name: <input type="text" name="last_name"><br>
                Date of Birth: <input type="date" name="dob"><br>
                ID File 1: <input type="file" name="file1"><br>
                ID File 2: <input type="file" name="file2"><br>
                <input type="submit" value="Submit KYC">
            </form>
        '''
    else:
        country = request.form['country']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        dob = request.form['dob']
        file1 = request.files['file1']
        file2 = request.files['file2']

        # Save files and KYC details to the database
        # Send the KYC details to the Discord bot
        data = {
            "country": country,
            "first_name": first_name,
            "last_name": last_name,
            "dob": dob,
            "file1_url": "URL_TO_FILE1",
            "file2_url": "URL_TO_FILE2"
        }
        requests.post(DISCORD_WEBHOOK_URL, json=data)
        return "KYC submitted successfully!"

if __name__ == '__main__':
    app.run(port=5000, debug=True)
