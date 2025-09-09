"""
backend_app.py

Handle some CRUD operations, GET, PUT, POST, DELETE.
Additional sort the blog posts via query parameters.
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_swagger_ui import get_swaggerui_blueprint
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
import json as js
import os


app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes


limiter = Limiter(
    app=app,
    key_func=get_remote_address,  # Limit per IP address
    default_limits=["100 per hour"] # 100 requests per hour
)


SWAGGER_URL = "/api/docs"   # URL for the documentation
API_URL = "/static/masterblog.json" # JSON file with definitions

swagger_ui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': 'Masterblog API'}
)
app.register_blueprint(swagger_ui_blueprint,
                       url_prefix=SWAGGER_URL)

DATA_FILE = os.path.join(os.path.dirname(__file__),
                         "data", "blog_storage.json")


def load_posts():
    """Load and read the posts from json."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r") as file:
            return js.load(file)
    except (js.JSONDecodeError, FileNotFoundError):
        print("JSON or File not found!")
        return []


def save_posts(posts):
    """Write the new data to json."""
    with open(DATA_FILE, "w") as file:
        js.dump(posts, file, indent=4)


@app.get('/api/posts')
def get_posts():
    """Get the list of posts."""
    posts = load_posts()
    # Get the query parameter
    sort_field = request.args.get("sort")
    direction = request.args.get("direction", "asc")

    # Validate parameters
    if sort_field and sort_field not in ["title", "content"]:
        abort(400, description="Invalid sort field")
    if direction not in ["asc", "desc"]:
        abort(400, description="Invalid sort direction")

    # Copy the posts to save the original direction
    posts_copy = load_posts()

    # Optional sorting
    if sort_field:
        reverse = direction == "desc"
        posts_copy.sort(key=lambda p: p[sort_field],
                        reverse=reverse)

    # Pagination configuration
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    start = (page - 1) * limit
    end = start + limit
    paginated_posts = posts_copy[start:end]

    return jsonify(paginated_posts)


@app.post("/api/posts")
@limiter.limit("10 per minute")
def add_post():
    """Create a new blog post."""
    posts = load_posts()
    data = request.get_json()

    # Validate input
    missing = [field for field in ("title", "content")
               if field not in data or not data[field]]
    if missing:
        abort(400, description=f"Missing field: "
                               f"{', '.join(missing)}")

    # Generate new ID
    new_id = max((post["id"] for post in posts), default=0) + 1

    # Create new post
    new_post = {
        "id": new_id,
        "title": data["title"],
        "content": data["content"]
    }
    posts.append(new_post)
    save_posts(posts)

    return jsonify(new_post), 201


@app.delete("/api/posts/<int:post_id>")
def delete_post(post_id):
    """Remove a post."""
    posts = load_posts()
    # Find the post
    post = next((post for post in posts
                 if post['id'] == post_id), None)
    if not post:
        abort(404, description="Post not found")

    posts = [post for post in posts
             if post['id'] != post_id]
    save_posts(posts)
    return jsonify({"message": "Post deleted"}), 200


@app.put("/api/posts/<int:post_id>")
def update_post(post_id):
    """Make some changes by an existing post."""
    posts = load_posts()
    data = request.get_json()

    # Validation
    if not data or "title" not in data or "content" not in data:
        abort(400, description="Missing title or content")

    # Find post
    for item, post in enumerate(posts):
        if post['id'] == post_id:
            posts[item] = {
                "id": post_id,
                "title": data['title'],
                "content": data['content']
            }
            save_posts(posts)
            return jsonify(posts[item]), 200

    abort(404, description="Post not found")


@app.get("/api/posts/search")
def search_posts():
    """Search posts with ah query parameter by title or content."""
    posts = load_posts()
    title_query = request.args.get("title", "").lower()
    content_query = request.args.get("content", "").lower()

    # Filter the posts
    results = [
        post for post in posts
        if (title_query in post['title'].lower()
            if title_query else False)
        or (content_query in post['content'].lower()
            if content_query else False)
    ]
    return jsonify(results), 200


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"status": 400,
                    "message": str(error)}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": 404,
                    "message": "Resource not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"status": 500,
                    "message": "Internal Server Error"}), 500



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5002, debug=True)
