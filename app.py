from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello from Flask!"

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if username == "jannik" and password == "1234":
        return jsonify({"status": "success", "message": "Login ok!"})
    else:
        return jsonify({"status": "fail", "message": "Falsche Daten"}), 401

if __name__ == '__main__':
    app.run()
