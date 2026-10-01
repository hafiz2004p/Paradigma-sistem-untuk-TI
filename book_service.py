from flask import Flask, jsonify

app = Flask(__name__)

# Database khusus Book Service
books = [{"id": 1, "title": "Belajar Flask", "stock": 5}]

@app.route('/books', methods=['GET'])
def get_books():
    return jsonify(books)

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    for b in books:
        if b['id'] == book_id:
            return jsonify(b)
    return jsonify({"error": "Not found"}), 404

# --- ROUTE BARU: untuk mengurangi stok ---
@app.route('/books/<int:book_id>/reduce-stock', methods=['PUT'])
def reduce_stock(book_id):
    for b in books:
        if b['id'] == book_id:
            if b['stock'] > 0:
                b['stock'] -= 1
                return jsonify(b), 200
            return jsonify({"error": "Stok habis"}), 400
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    app.run(port=5001, debug=True)