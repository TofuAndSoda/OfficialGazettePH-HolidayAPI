from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import time
import socket
from datetime import datetime
import random
import os  # for getting the PORT from Render

# ✅ List of user agents to make the request look like a real browser
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
]

app = Flask(__name__)

@app.route('/', methods=['GET'])
@app.route('/holidays', methods=['GET'])
@app.route('/holidays/<int:year>', methods=['GET'])
def get_holidays(year=datetime.now().year):
    start_time = time.time()

    url = f'https://www.officialgazette.gov.ph/nationwide-holidays/{year}/'
    domain = url.split("//")[-1].split("/")[0]
    
    # Try to resolve the domain name
    try:
        ip_address = socket.gethostbyname(domain)
    except socket.gaierror:
        return jsonify({'error': 'Failed to resolve domain name'})

    # ✅ Add full browser-like headers to avoid 403
    headers = {
        "User-Agent": random.choice(user_agents),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive"
    }

    # ✅ Attempt to fetch data
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.ConnectionError:
        return jsonify({'error': 'Failed to connect to the source URL'})
    except requests.Timeout:
        return jsonify({'error': 'Request to the source URL timed out'})
    except requests.RequestException as e:
        return jsonify({'error': f'Request failed: {e}'})

    if response.status_code != 200:
        return jsonify({'error': f'Failed to retrieve data, status code: {response.status_code}'})

    # ✅ Parse the HTML with BeautifulSoup
    try:
        soup = BeautifulSoup(response.content, 'html.parser')
        holidays = []

        tables = soup.find_all("table")
        for i, table in enumerate(tables):
            holiday_type = "Regular Holidays" if i == 0 else "Special (Non-Working) Holidays"
            rows = table.find_all('tr')
            for row in rows[1:]:
                cols = row.find_all('td')
                if len(cols) < 2:
                    continue
                event = cols[0].get_text(strip=True)
                date = cols[1].get_text(strip=True)
                holidays.append({'event': event, 'date': date, 'type': holiday_type})

    except Exception as e:
        return jsonify({'error': f'Error processing HTML content: {e}'})

    response_time = time.time() - start_time
    return jsonify({
        'request_timestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start_time)),
        'response_duration_seconds': round(response_time, 2),
        'source_url': url,
        'source_ip': ip_address,
        'number_of_holidays': len(holidays),
        'holidays': holidays
    })

# ✅ Use this block to work on Render (bind to PORT and 0.0.0.0)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
