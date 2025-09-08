from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

POSTS = [
    {"id": 1, "title": "First post", "content": "This is the first post."},
    {"id": 2, "title": "Second post", "content": "This is the second post."},
]


@app.get('/api/posts')
def get_posts():
    return jsonify(POSTS)


@app.post("/api/posts")
def add_post():
    data = request.get_json()

    # Validate input
    missing = [field for field in ("title", "content")
               if field not in data or not data[field]]
    if missing:
        return jsonify({"error": f"Missing field: "
                                 f"{', '.join(missing)}"}), 400

    # Generate new ID
    new_id = max((post['id'] for post in POSTS), default=0) + 1

    # Create new post
    new_post = {
        "id": new_id,
        "title": data['title'],
        "content": data['content']
    }
    POSTS.append(new_post)

    return jsonify(new_post), 201



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
