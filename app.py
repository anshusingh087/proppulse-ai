from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
DB_NAME = "predictions.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            locality TEXT,
            area REAL,
            bhk INTEGER,
            down_payment REAL,
            estimated_price TEXT,
            monthly_emi TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    locality = data.get('locality', 'Whitefield')
    area = float(data.get('area', 1200))
    bhk = int(data.get('bhk', 2))
    down_payment = float(data.get('down_payment', 20))
    rate = float(data.get('rate', 9800))

    # Valuation Formula
    bhk_multiplier = 1 + ((bhk - 2) * 0.06)
    total_val = round(area * rate * bhk_multiplier)

    # Loan & EMI Calculation
    loan_amt = total_val * ((100 - down_payment) / 100)
    monthly_rate = 8.5 / 12 / 100
    months = 240
    emi = round((loan_amt * monthly_rate * pow(1 + monthly_rate, months)) / (pow(1 + monthly_rate, months) - 1))
    five_year = round(total_val * pow(1 + 0.085, 5))

    # Formatting Price
    if total_val >= 10000000:
        price_str = f"₹ {(total_val / 10000000):.2f} Cr"
    else:
        price_str = f"₹ {(total_val / 100000):.2f} Lac"

    emi_str = f"₹ {emi:,}"
    time_str = datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Save to SQLite Database
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO history (timestamp, locality, area, bhk, down_payment, estimated_price, monthly_emi)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (time_str, locality, area, bhk, down_payment, price_str, emi_str))
    conn.commit()
    conn.close()

    return jsonify({
        'price': price_str,
        'emi': emi_str,
        'five_year': f"₹ {(five_year / 10000000):.2f} Cr" if five_year >= 10000000 else f"₹ {(five_year / 100000):.2f} Lac",
        'rate': f"₹ {int(rate):,}"
    })

@app.route('/history', methods=['GET'])
def get_history():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT timestamp, locality, area, bhk, estimated_price, monthly_emi FROM history ORDER BY id DESC LIMIT 8')
    rows = cursor.fetchall()
    conn.close()

    history_data = []
    for r in rows:
        history_data.append({
            'time': r[0],
            'locality': r[1],
            'area': r[2],
            'bhk': r[3],
            'price': r[4],
            'emi': r[5]
        })
    return jsonify(history_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
