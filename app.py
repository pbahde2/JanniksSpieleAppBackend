import os
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from passlib.hash import bcrypt
from datetime import timedelta


app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = "supersecret"  # ÄNDERN in Produktion!
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)  # 1 Tag

jwt = JWTManager(app)

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def is_expired(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d") < datetime.today()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    user = users.get(username)

    if not user:
        return jsonify({"msg": "User nicht gefunden"}), 401

    if is_expired(user["expires"]):
        return jsonify({"msg": "Zugriff abgelaufen"}), 403

    if not bcrypt.verify(password, user["password"]):
        return jsonify({"msg": "Falsches Passwort"}), 401
    # Identity als String erstellen, z.B. eine Kombination aus Username und Rolle
    identity = f"{username}:{user.get('role', 'user')}"  # Optional kannst du auch eine andere Zeichenfolge verwenden
    # JWT-Token erstellen
    token = create_access_token(identity=identity)
    return jsonify(access_token=token)

@app.route('/api/user', methods=['POST'])
@jwt_required()
def add_user():
    current = get_jwt_identity()
    username, role = current.split(":")

    if role != "admin":
        return jsonify({"msg": "Nur Admin erlaubt"}), 403

    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    expires = data.get("expires")
    role = data.get("role", "user")

    users = load_users()
    if username in users:
        return jsonify({"msg": "Benutzer existiert bereits"}), 400

    users[username] = {
        "password": bcrypt.hash(password),
        "expires": expires,
        "role": role
    }
    save_users(users)
    return jsonify({"msg": "Benutzer angelegt"}), 201

@app.route('/api/user/<username>', methods=['PUT'])
@jwt_required()
def update_user(username):
    current = get_jwt_identity()
    currentuser, role = current.split(":")

    if role != "admin":
        return jsonify({"msg": "Nur Admin erlaubt"}), 403

    data = request.get_json()
    new_password = data.get("password")
    new_expires = data.get("expires")

    users = load_users()
    if username not in users:
        return jsonify({"msg": "Benutzer nicht gefunden"}), 404

    if new_password:
        users[username]["password"] = bcrypt.hash(new_password)
    if new_expires:
        users[username]["expires"] = new_expires

    save_users(users)
    return jsonify({"msg": "Benutzer aktualisiert"})

@app.route('/api/user/<username>', methods=['DELETE'])
@jwt_required()
def delete_user(username):       
    current = get_jwt_identity()
    currentUser, role = current.split(":")
    
    if role != "admin":
        return jsonify({"msg": "Nur Admin erlaubt"}), 403

    users = load_users()
    if username not in users:
        return jsonify({"msg": "Benutzer nicht gefunden"}), 404

    del users[username]  
    save_users(users)          
    return jsonify({"msg": f"Benutzer '{username}' wurde gelöscht"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
