from flask import Flask, render_template, request, jsonify
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize local SQLite database
def init_db():
    conn = sqlite3.connect('history.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT,
            sqft REAL,
            bhk INTEGER,
            price TEXT,
            rent TEXT,
            emi TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Locality benchmark data (rate, rental multiplier, transit score)
LOCALITY_DATA = {
    "Indiranagar": {"rate": 14500, "rent_rate": 36, "metro": "4.9/5", "growth": "+12.4%", "tag": "Prime Hub"},
    "Koramangala": {"rate": 13800, "rent_rate": 34, "metro": "4.6/5", "growth": "+11.1%", "tag": "Commercial Core"},
    "HSR Layout": {"rate": 9800, "rent_rate": 28, "metro": "4.5/5", "growth": "+14.2%", "tag": "High ROI Zone"},
    "Whitefield": {"rate": 7800, "rent_rate": 23, "metro": "4.8/5", "growth": "+16.8%", "tag": "IT Corridor"},
    "Sarjapur Road": {"rate": 7400, "rent_rate": 22, "metro": "4.1/5", "growth": "+15.0%", "tag": "High Growth"},
    "Hebbal": {"rate": 8900, "rent_rate": 25, "metro": "4.4/5", "growth": "+13.5%", "tag": "North Gateway"},
    "Marathahalli": {"rate": 6900, "rent_rate": 21, "metro": "4.2/5", "growth": "+9.8%", "tag": "Affordable IT Hub"},
    "Electronic City": {"rate": 5400, "rent_rate": 18, "metro": "4.7/5", "growth": "+10.2%", "tag": "Tech Industrial"}
}

@app.route('/')
def home():
    return render_template('index.html', localities=list(LOCALITY_DATA.keys()))

@app.route('/predict_analytics', methods=['POST'])
def predict_analytics():
    try:
        sqft = float(request.form.get('sqft', 1200))
        bhk = int(request.form.get('bhk', 2))
        bath = int(request.form.get('bath', 2))
        location = request.form.get('location', 'Whitefield')
        furnishing = request.form.get('furnishing', 'Semi-Furnished')

        loc_info = LOCALITY_DATA.get(location, {"rate": 7000, "rent_rate": 22, "metro": "4.0/5", "growth": "+10%", "tag": "Emerging"})
        rate_per_sqft = loc_info["rate"]

        # Base valuation formula
        base_cost = sqft * rate_per_sqft
        bhk_factor = 1.0 + (bhk * 0.05) + (bath * 0.02)
        furnish_factor = 1.08 if furnishing == 'Semi-Furnished' else (1.18 if furnishing == 'Fully-Furnished' else 1.0)
        
        total_valuation = base_cost * bhk_factor * furnish_factor
        price_lakhs = round(total_valuation / 100000, 2)

        # EMI and loan analytics (80% loan, 8.5% interest, 20-year tenure)
        principal = total_valuation * 0.80
        rate_monthly = 8.5 / (12 * 100)
        tenure_months = 240
        emi = principal * rate_monthly * ((1 + rate_monthly)**tenure_months) / (((1 + rate_monthly)**tenure_months) - 1)
        total_payable = emi * tenure_months
        total_interest = total_payable - principal

        # Rental yield and monthly rent calculation
        monthly_rent = (sqft * loc_info["rent_rate"]) * (1.1 if furnishing == 'Semi-Furnished' else (1.25 if furnishing == 'Fully-Furnished' else 1.0))
        rental_yield = round(((monthly_rent * 12) / total_valuation) * 100, 2)

        # Log entry into database
        timestamp = datetime.now().strftime("%d %b, %H:%M")
        conn = sqlite3.connect('history.db')
        cur = conn.cursor()
        cur.execute('''INSERT INTO searches (location, sqft, bhk, price, rent, emi, timestamp)
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (location, sqft, bhk, f"Rs. {price_lakhs} L", f"Rs. {int(monthly_rent):,}/mo", f"Rs. {int(emi):,}/mo", timestamp))
        conn.commit()
        conn.close()

        return jsonify({
            'status': 'success',
            'location': location,
            'tag': loc_info["tag"],
            'metro': loc_info["metro"],
            'growth': loc_info["growth"],
            'rate_per_sqft': f"Rs. {rate_per_sqft:,}",
            'price_lakhs': f"Rs. {price_lakhs} Lakhs",
            'monthly_rent': f"Rs. {int(round(monthly_rent)):,}",
            'rental_yield': f"{rental_yield}%",
            'emi': f"Rs. {int(round(emi)):,}",
            'principal_raw': round(principal),
            'interest_raw': round(total_interest)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/get_history', methods=['GET'])
def get_history():
    conn = sqlite3.connect('history.db')
    cur = conn.cursor()
    cur.execute("SELECT location, sqft, bhk, price, rent, emi, timestamp FROM searches ORDER BY id DESC LIMIT 5")
    rows = cur.fetchall()
    conn.close()
    
    return jsonify({
        'history': [{'location': r[0], 'sqft': r[1], 'bhk': r[2], 'price': r[3], 'rent': r[4], 'emi': r[5], 'time': r[6]} for r in rows]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)