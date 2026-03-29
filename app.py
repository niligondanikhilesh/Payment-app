from flask import Flask, request, jsonify
from redis import Redis
import psycopg2
import os
import uuid
import time

app = Flask(__name__)
cache = Redis(host=os.environ.get("REDIS_HOST", "redis"), port=6379)

def get_db():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres"),
        database=os.environ.get("DB_NAME", "payquick"),
        user=os.environ.get("DB_USER", "admin"),
        password=os.environ.get("DB_PASSWORD", "password")
    )

def init_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id VARCHAR(50) PRIMARY KEY,
                sender VARCHAR(100),
                receiver VARCHAR(100),
                amount FLOAT,
                status VARCHAR(50),
                created_at FLOAT
            );
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

@app.route("/")
def home():
    return jsonify({
        "service": "PayQuick Payment API",
        "version": "1.0.0",
        "status": "running"
    })

@app.route("/pay", methods=["POST"])
def pay():
    init_db()
    data = request.json
    if not data or 'sender' not in data or 'receiver' not in data or 'amount' not in data:
        return jsonify({"error": "sender, receiver and amount required!"}), 400

    transaction_id = str(uuid.uuid4())[:8].upper()
    transaction = {
        "id": transaction_id,
        "sender": data["sender"],
        "receiver": data["receiver"],
        "amount": data["amount"],
        "status": "SUCCESS",
        "created_at": time.time()
    }

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO transactions (id, sender, receiver, amount, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (transaction_id, data["sender"], data["receiver"], data["amount"], "SUCCESS", time.time()))
        conn.commit()
        conn.close()
        cache.delete("transactions")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "transaction_id": transaction_id,
        "status": "SUCCESS ✅",
        "message": f"Payment of ₹{data['amount']} sent from {data['sender']} to {data['receiver']}"
    })

@app.route("/transactions")
def transactions():
    init_db()
    cached = cache.get("transactions")
    if cached:
        import json
        return jsonify({"source": "cache 🚀", "data": json.loads(cached)})

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM transactions ORDER BY created_at DESC;")
        rows = cur.fetchall()
        conn.close()
        data = [{"id": r[0], "sender": r[1], "receiver": r[2], "amount": r[3], "status": r[4]} for r in rows]
        import json
        cache.set("transactions", json.dumps(data), ex=60)
        return jsonify({"source": "database 🗄️", "data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/balance/<user>")
def balance(user):
    cached = cache.get(f"balance:{user}")
    if cached:
        return jsonify({"user": user, "balance": float(cached), "source": "cache 🚀"})

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE receiver=%s;", (user,))
        received = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE sender=%s;", (user,))
        sent = cur.fetchone()[0]
        conn.close()
        balance = float(received) - float(sent)
        cache.set(f"balance:{user}", balance, ex=30)
        return jsonify({"user": user, "balance": balance, "source": "database 🗄️"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
