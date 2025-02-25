

from flask import Flask, request, jsonify
from flask_cors import CORS
from jose import jwt
from datetime import datetime, timedelta
from git import Repo
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

repo_path = os.path.dirname(os.path.abspath(__file__))
repo = Repo(repo_path)

# File to store posts
POSTS_FILE = 'posts.json'

def git_push_changes():
    try:
        repo.git.add('public/posts.json')
        repo.git.commit('-m', 'Update blog posts')
        repo.git.push('origin', 'main')
        return True
    except Exception as e:
        print(f"Push failed: {str(e)}")
        return False

# Load posts from file
# Initialize posts from file
def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    return []

# Save posts to file
if not os.path.exists('public'):
    os.makedirs('public')

def save_posts(posts):
    # Save to both storage files
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f)
    
    # Save static version for GitHub Pages
    with open('public/posts.json', 'w') as f:
        json.dump(posts, f)

# Initialize posts from file
global posts
posts = load_posts()
save_posts(posts)

SECRET_KEY = os.getenv('SECRET_KEY')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
print("SECRET_KEY loaded:", bool(SECRET_KEY))  # Should print True if key exists

def create_token(username: str):
    expiration = datetime.utcnow() + timedelta(hours=24)
    data = {"sub": username, "exp": expiration}
    token = jwt.encode(data, SECRET_KEY, algorithm="HS256")
    return token

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        token = create_token(username)
        return jsonify({"token": token})
    return jsonify({"message": "Invalid credentials"}), 401

@app.route('/api/verify', methods=['GET'])
def verify():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"message": "No token provided"}), 401
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return jsonify({"authenticated": True})
    except:
        return jsonify({"message": "Invalid token"}), 403

@app.route('/api/posts', methods=['GET'])
def get_posts():
    return jsonify(posts)

@app.route('/api/posts', methods=['POST'])
def create_post():
    global posts
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"message": "No token provided"}), 401
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        new_post = request.json
        new_post['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not isinstance(posts, list):
            posts = []
            
        posts.insert(0, new_post)
        save_posts(posts)
        git_push_changes()
        return jsonify({"message": "Post created and published successfully"})
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"message": "Error publishing post"}), 403
        
if __name__ == '__main__':    
    app.run(port=3000)