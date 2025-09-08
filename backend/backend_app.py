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


@app.delete("/api/posts/<int:post_id>")
def delete_post(post_id):
    global POSTS
    # Find the post
    post = next((post for post in POSTS if post['id'] == post_id), None)
    if not post:
        return jsonify({"error": "Post not found"}), 404

    POSTS = [post for post in POSTS if post['id'] != post_id]
    return jsonify({"message": "Post deleted"}), 200


@app.put("/api/posts/<int:post_id>")
def update_post(post_id):
    global POSTS
    data = request.get_json()

    # Validation
    if not data or "title" not in data or "content" not in data:
        return jsonify({"error": "Missing title or content"}), 400

    # Find post
    for item, post in enumerate(POSTS):
        if post['id'] == post_id:
            POSTS[item] = {
                "id": post_id,
                "title": data['title'],
                "content": data['content']
            }
            return jsonify(POSTS[item]), 200

    return jsonify({"error": "Post not found"}), 404


@app.get("/api/posts/search")
def search_posts():
    title_query = request.args.get("title", "").lower()
    content_query = request.args.get("content", "").lower()

    # Filter the posts
    results = [
        post for post in POSTS
        if (title_query in post['title'].lower()
            if title_query else False)
        or (content_query in post['content'].lower()
            if content_query else False)
    ]
    return jsonify(results), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
