from flask import Flask, request, jsonify, redirect, abort
import hashlib
import threading

app = Flask(__name__)

# In-memory store for URLs
url_store = {}
lock = threading.Lock()

# Base url for the shortened links
BASE_URL = "http://localhost:8080/"

def generate_short_key(url):
    # Using SHA-1
    hash_object = hashlib.sha1(url.encode())
    short_key = hash_object.hexdigest()[:6]
    return short_key

@app.route('/', methods=['POST'])
def shorten_url():
    data = request.get_json()
    if 'url' not in data:
        return jsonify({"error": "Missing field: url"}), 400

    long_url = data['url']

    with lock:
        # Check if url already exists in the store
        for key, stored_url in url_store.items():
            if stored_url == long_url:
                return jsonify({
                    "key": key,
                    "long_url": long_url,
                    "short_url": f"{BASE_URL}{key}"
                }), 200

        # Generate a new short key and store the URL
        short_key = generate_short_key(long_url)
        while short_key in url_store:
            short_key = generate_short_key(long_url + short_key)  # Ensure no collision

        url_store[short_key] = long_url

        return jsonify({
            "key": short_key,
            "long_url": long_url,
            "short_url": f"{BASE_URL}{short_key}"
        }), 201

@app.route('/<key>', methods=['GET'])
def redirect_url(key):
    with lock:
        long_url = url_store.get(key)
        if long_url:
            return redirect(long_url, code=302)
        else:
            return jsonify({"error": "URL not found"}), 404

@app.route('/<key>', methods=['DELETE'])
def delete_url(key):
    with lock:
        if key in url_store:
            del url_store[key]
        return '', 200

def main():
    app.run(port=8080, debug=True)


if __name__ == "__main__":
    main()
