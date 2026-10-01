# Flask Monolith vs Microservices

Proyek hands-on untuk memahami perbedaan arsitektur **Monolith** dan **Microservices** menggunakan Flask (Python), sebagai bagian dari praktikum mata kuliah **Paradigma Sistem untuk IT** — Program Studi Teknologi Rekayasa Komputer dan Jaringan, Politeknik Negeri Lhokseumawe.

## Daftar Isi

- [Konsep Dasar](#konsep-dasar)
- [Struktur Proyek](#struktur-proyek)
- [Persiapan Lingkungan](#persiapan-lingkungan)
- [Bagian 1: Monolith](#bagian-1-monolith)
- [Bagian 2: Microservices](#bagian-2-microservices)
- [Eksperimen Fault Isolation](#eksperimen-fault-isolation)
- [Bahan Diskusi](#bahan-diskusi)
- [Kesimpulan](#kesimpulan)

## Konsep Dasar

**Monolith**: Seluruh fitur aplikasi (katalog buku, pembayaran, pesanan) disatukan dalam satu codebase dan berjalan di satu server/proses yang sama.

**Microservices**: Fitur aplikasi dipecah menjadi layanan-layanan kecil yang mandiri (Book Service dan Order Service). Setiap layanan berjalan di server/port masing-masing dan saling berkomunikasi via HTTP/API.

## Struktur Proyek

```
flask-project/
├── monolith_app.py      # Aplikasi Monolith (port 5000)
├── book_service.py      # Microservice - layanan Buku (port 5001)
├── order_service.py     # Microservice - layanan Pesanan (port 5002)
└── README.md
```

## Persiapan Lingkungan

Dikerjakan di **Ubuntu Linux** menggunakan **VS Code**.

### 1. Buat direktori proyek

```bash
cd ~
mkdir flask-project
cd flask-project
```

### 2. Install dependencies

```bash
pip install Flask requests --break-system-packages
```

> Flag `--break-system-packages` diperlukan di Ubuntu versi baru (Python 3.12+) karena kebijakan *externally-managed-environment* (PEP 668).

**Output yang diharapkan** (potongan akhir log instalasi):

```
Installing collected packages: werkzeug, itsdangerous, blinker, Flask
Successfully installed Flask-3.1.3 blinker-1.9.0 itsdangerous-2.2.0 werkzeug-3.1.9
```

### 3. Buka proyek di VS Code

```bash
code .
```

## Bagian 1: Monolith

Seluruh rute dan logika bisnis (Buku dan Pesanan) digabung dalam satu file: `monolith_app.py`.

### Kode `monolith_app.py`

```python
from flask import Flask, jsonify, request

app = Flask(__name__)

# Database bohongan (In-memory)
books = [{"id": 1, "title": "Belajar Flask", "stock": 5}]
orders = []

# --- FITUR BUKU ---
@app.route('/books', methods=['GET'])
def get_books():
    return jsonify(books)

# --- FITUR PESANAN ---
@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    book_id = data.get('book_id')
    # Logika bisnis: Cek stok buku langsung dari variabel global
    for b in books:
        if b['id'] == book_id and b['stock'] > 0:
            b['stock'] -= 1
            order = {"id": len(orders)+1, "book_id": book_id, "status": "berhasil"}
            orders.append(order)
            return jsonify(order), 201
    return jsonify({"error": "Buku tidak ditemukan atau stok habis"}), 400

if __name__ == '__main__':
    # Aplikasi berjalan di port 5000
    app.run(port=5000, debug=True)
```

### Menjalankan

```bash
python3 monolith_app.py
```

**Output yang diharapkan di terminal:**

```
 * Serving Flask app 'monolith_app'
 * Debug mode: on
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

Server berjalan di `http://127.0.0.1:5000`. **Biarkan terminal ini tetap terbuka**, buka terminal baru untuk pengujian.

### Pengujian

**1. Cek daftar buku (kondisi awal):**

```bash
curl http://localhost:5000/books
```

Output yang harus keluar:

```json
[
  {
    "id": 1,
    "stock": 5,
    "title": "Belajar Flask"
  }
]
```

**2. Buat pesanan:**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"book_id": 1}' http://localhost:5000/orders
```

Output yang harus keluar:

```json
{
  "book_id": 1,
  "id": 1,
  "status": "berhasil"
}
```

**3. Cek stok setelah pesanan (harus berkurang otomatis):**

```bash
curl http://localhost:5000/books
```

Output yang harus keluar:

```json
[
  {
    "id": 1,
    "stock": 4,
    "title": "Belajar Flask"
  }
]
```

**4. Coba pesan terus sampai stok habis (5x berturut-turut), lalu pesan ke-6:**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"book_id": 1}' http://localhost:5000/orders
```

Output yang harus keluar setelah stok habis:

```json
{
  "error": "Buku tidak ditemukan atau stok habis"
}
```

**Penjelasan**: stok berkurang otomatis setiap kali pesanan berhasil, karena variabel `books` dan `orders` berada dalam satu ruang memori/proses yang sama (ciri khas Monolith).

## Bagian 2: Microservices

Sistem dipecah menjadi dua layanan independen. Order Service tidak bisa lagi membaca variabel `books` secara langsung — harus memanggil Book Service via HTTP Request.

### Kode `book_service.py` (port 5001)

```python
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

if __name__ == '__main__':
    # Book service berjalan di port 5001
    app.run(port=5001, debug=True)
```

### Kode `order_service.py` (port 5002)

```python
from flask import Flask, jsonify, request
import requests

app = Flask(__name__)
orders = []
BOOK_SERVICE_URL = "http://localhost:5001"  # Alamat Book Service

@app.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    book_id = data.get('book_id')

    # Komunikasi antar service: Tanya Book Service apakah buku ada
    try:
        response = requests.get(f"{BOOK_SERVICE_URL}/books/{book_id}")
        if response.status_code == 200:
            book_data = response.json()
            if book_data['stock'] > 0:
                order = {"id": len(orders)+1, "book_id": book_id, "status": "berhasil"}
                orders.append(order)
                return jsonify(order), 201

        return jsonify({"error": "Buku tidak tersedia"}), 400
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Book Service sedang down!"}), 500

if __name__ == '__main__':
    # Order service berjalan di port 5002
    app.run(port=5002, debug=True)
```

### Menjalankan kedua layanan

**Terminal 1:**

```bash
python3 book_service.py
```

Output yang diharapkan:

```
 * Serving Flask app 'book_service'
 * Debug mode: on
 * Running on http://127.0.0.1:5001
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

**Terminal 2:**

```bash
python3 order_service.py
```

Output yang diharapkan:

```
 * Serving Flask app 'order_service'
 * Debug mode: on
 * Running on http://127.0.0.1:5002
Press CTRL+C to quit
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: xxx-xxx-xxx
```

### Pengujian (terminal ketiga)

**1. Cek daftar buku via Book Service:**

```bash
curl http://localhost:5001/books
```

Output yang harus keluar:

```json
[
  {
    "id": 1,
    "stock": 5,
    "title": "Belajar Flask"
  }
]
```

**2. Cek detail satu buku:**

```bash
curl http://localhost:5001/books/1
```

Output yang harus keluar:

```json
{
  "id": 1,
  "stock": 5,
  "title": "Belajar Flask"
}
```

**3. Buat pesanan lewat Order Service (port 5002):**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"book_id": 1}' http://localhost:5002/orders
```

Output yang harus keluar:

```json
{
  "book_id": 1,
  "id": 1,
  "status": "berhasil"
}
```

**4. Cek lagi stok buku di Book Service:**

```bash
curl http://localhost:5001/books
```

> **Catatan penting**: pada kode `book_service.py` dan `order_service.py` versi dasar di atas, Order Service **hanya membaca** stok Book Service (GET), tidak ada perintah untuk menguranginya. Jadi secara default, stok di Book Service **tidak otomatis berkurang** meskipun pesanan berhasil dibuat — outputnya akan tetap:
>
> ```json
> [
>   {
>     "id": 1,
>     "stock": 5,
>     "title": "Belajar Flask"
>   }
> ]
> ```
>
> Ini adalah poin pembelajaran penting: di Microservices, setiap perubahan data pada layanan lain harus dikomunikasikan secara eksplisit lewat API. Beda dengan Monolith yang otomatis konsisten karena berbagi memori yang sama. (Lihat bagian [Pengembangan Tambahan](#pengembangan-tambahan-opsional) jika ingin stok benar-benar berkurang.)

## Eksperimen Fault Isolation

Tujuan: membuktikan bahwa kegagalan satu layanan tidak menjatuhkan layanan lain.

### Langkah

**1. Matikan `book_service.py`** — tekan `Ctrl+C` di Terminal 1.

**2. Kirim ulang permintaan pesanan ke `order_service.py`:**

```bash
curl -X POST -H "Content-Type: application/json" -d '{"book_id": 1}' http://localhost:5002/orders
```

### Output yang harus keluar

```json
{
  "error": "Book Service sedang down!"
}
```

(dengan HTTP status code `500`)

**Penjelasan**: Order Service **tetap hidup** dan merespons dengan pesan error yang elegan, bukan ikut crash. Inilah yang disebut **Fault Isolation** — kegagalan pada satu layanan tidak merambat ke layanan lain yang independen.

## Pengembangan Tambahan (Opsional)

Jika ingin stok di Microservices benar-benar berkurang setelah pesanan berhasil, tambahkan endpoint berikut.

**Tambahan di `book_service.py`:**

```python
@app.route('/books/<int:book_id>/reduce-stock', methods=['PUT'])
def reduce_stock(book_id):
    for b in books:
        if b['id'] == book_id:
            if b['stock'] > 0:
                b['stock'] -= 1
                return jsonify(b), 200
            return jsonify({"error": "Stok habis"}), 400
    return jsonify({"error": "Not found"}), 404
```

**Tambahan di `order_service.py`** (dipanggil setelah stok dicek tersedia, sebelum order dibuat):

```python
reduce_response = requests.put(f"{BOOK_SERVICE_URL}/books/{book_id}/reduce-stock")
if reduce_response.status_code != 200:
    return jsonify({"error": "Gagal mengurangi stok"}), 500
```

Setelah ditambahkan, pengujian `curl http://localhost:5001/books` setelah satu pesanan berhasil akan menghasilkan:

```json
[
  {
    "id": 1,
    "stock": 4,
    "title": "Belajar Flask"
  }
]
```

## Bahan Diskusi

### 1. Jika fitur Pesanan di Monolith crash fatal, apa yang terjadi pada fitur Buku?

Pada Monolith, seluruh fitur berjalan dalam satu proses/memori yang sama, sehingga bug fatal di fitur Pesanan berpotensi menjatuhkan seluruh aplikasi, termasuk fitur Buku. Pada Microservices, Book Service dan Order Service berjalan sebagai proses terpisah (port 5001 vs 5002), sehingga kegagalan di satu layanan tidak memengaruhi layanan lain — terbukti dari eksperimen Fault Isolation di atas.

### 2. Solusi mengatasi latensi HTTP antar-service di industri nyata

- **Caching** (misalnya Redis) — menyimpan hasil respons sementara agar tidak selalu memanggil service lain.
- **Asynchronous Messaging** (RabbitMQ, Kafka) — komunikasi non-blocking antar-layanan.
- **gRPC** — protokol biner yang lebih cepat dibanding REST/JSON.
- **Service Mesh** (Istio) — mengatur retry, timeout, dan load balancing otomatis.
- **Circuit Breaker Pattern** — mencegah sistem terus menunggu layanan yang lambat/down.

### 3. Traffic pencarian buku melonjak, layanan mana yang di-scale-up?

Karena Microservices memisahkan setiap fitur menjadi layanan independen, cukup **Book Service (port 5001)** yang perlu ditambah kapasitas/instance-nya. **Order Service (port 5002)** tidak perlu diubah karena tidak mengalami lonjakan traffic. Ini adalah keunggulan Microservices dibanding Monolith, yang harus scale seluruh aplikasi meski hanya satu fitur yang membutuhkan kapasitas lebih besar.

## Kesimpulan

| Aspek | Monolith | Microservices |
|---|---|---|
| Struktur kode | Satu codebase tunggal | Terpisah per layanan |
| Komunikasi data | Akses langsung (shared memory) | HTTP/API antar-layanan |
| Isolasi kegagalan | Rendah | Tinggi (fault isolation) |
| Kecepatan akses | Lebih cepat | Sedikit lebih lambat (network overhead) |
| Skalabilitas | Scale seluruh aplikasi | Scale per-layanan |

---
