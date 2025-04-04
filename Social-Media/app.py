from flask import Flask, jsonify, request
import requests
import heapq
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
TEST_SERVER_BASE_URL = os.getenv("TEST_SERVER_BASE_URL")

# Authentication token from env
AUTH_TOKEN = {
    "token_type": os.getenv("AUTH_TOKEN_TYPE"),
    "access_token": os.getenv("AUTH_ACCESS_TOKEN")
}

def get_auth_headers():
    """Get headers with authentication token"""
    return {
        "Authorization": f"{AUTH_TOKEN['token_type']} {AUTH_TOKEN['access_token']}"
    }

def get_all_users():
    """Get all users from the test server API"""
    url = f"{TEST_SERVER_BASE_URL}/users"
    headers = get_auth_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('users', {})
    return {}

def get_user_post_count(user_id):
    """Get the number of posts for a specific user"""
    url = f"{TEST_SERVER_BASE_URL}/users/{user_id}/posts"
    headers = get_auth_headers()
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return len(response.json().get('posts', []))
    return 0

def get_post_comments(post_id):
    """Get comments for a specific post"""
    url = f"{TEST_SERVER_BASE_URL}/posts/{post_id}/comments"
    headers = get_auth_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('comments', [])
    return []

def get_user_posts(user_id):
    """Get posts for a specific user"""
    url = f"{TEST_SERVER_BASE_URL}/users/{user_id}/posts"
    headers = get_auth_headers()
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('posts', [])
    return []

@app.route('/users', methods=['GET'])
def top_users():
    """Returns top five users with the highest number of posts"""
    users = get_all_users()
    user_posts = {}
    
    for user_id in users:
        post_count = get_user_post_count(user_id)
        user_posts[user_id] = post_count
    
    top_5_users = heapq.nlargest(5, user_posts.items(), key=lambda x: x[1])
    
    result = []
    for user_id, post_count in top_5_users:
        result.append({
            "id": user_id,
            "name": users.get(user_id),
            "post_count": post_count
        })
    
    return jsonify({"top_users": result})

@app.route('/posts', methods=['GET'])
def top_latest_posts():
    """Returns top posts based on query parameter"""
    post_type = request.args.get('type', 'latest')
    
    if post_type not in ['latest', 'popular']:
        return jsonify({"error": "Invalid type parameter. Accepted values: latest, popular"}), 400
    
    users = get_all_users()
    
    all_posts = []
    post_comments = {}
    
    for user_id in users:
        posts = get_user_posts(user_id)
        for post in posts:
            post_id = post.get('id')
            post['user_name'] = users.get(post.get('userid', ''))
            all_posts.append(post)
            comments = get_post_comments(post_id)
            post_comments[post_id] = len(comments)
    
    result = []
    
    if post_type == 'latest':
        sorted_posts = sorted(all_posts, key=lambda x: int(x.get('id', 0)), reverse=True)
        result = sorted_posts[:5]
    else:
        for post in all_posts:
            post['comment_count'] = post_comments.get(post.get('id'), 0)
        
        sorted_posts = sorted(all_posts, key=lambda x: x.get('comment_count', 0), reverse=True)
        max_comments = sorted_posts[0].get('comment_count', 0) if sorted_posts else 0
        result = [post for post in sorted_posts if post.get('comment_count', 0) == max_comments]
    
    return jsonify({"posts": result})

@app.errorhandler(Exception)
def handle_error(e):
    """Global error handler"""
    return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
