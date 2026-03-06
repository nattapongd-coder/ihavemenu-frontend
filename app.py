from flask import Flask, render_template, jsonify, request
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()

app = Flask(__name__)

# ตั้งค่า Recipe Service URL (สำหรับ local development หรือ Docker)
RECIPE_SERVICE_URL = os.getenv('RECIPE_SERVICE_URL', 'http://localhost:5001')

print(f"[INFO] Starting Frontend Service...")
print(f"[INFO] Recipe Service URL: {RECIPE_SERVICE_URL}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user-input')
def user_input_page():
    return render_template('userInput.html')

@app.route('/result', methods=['GET', 'POST'])
def result_page():
    return render_template('result.html')

@app.route('/api/recommend', methods=['POST'])
def proxy_recommend():
    """Proxy endpoint ที่ forward request ไป recipe-service"""
    try:
        data = request.get_json()
        
        print(f"[INFO] Proxying request to {RECIPE_SERVICE_URL}/api/recommend")
        print(f"[INFO] Request data: {data}")
        
        # Forward request ไป recipe-service
        response = requests.post(
            f'{RECIPE_SERVICE_URL}/api/recommend',
            json=data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"[INFO] Recipe Service Response Status: {response.status_code}")
        
        # Return response จาก recipe-service ไป client
        return response.json(), response.status_code
        
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] ไม่สามารถเชื่อมต่อ Recipe Service ที่ {RECIPE_SERVICE_URL}")
        return jsonify({
            "error": "ไม่สามารถเชื่อมต่อ Recipe Service",
            "msg": f"Recipe Service unavailable at {RECIPE_SERVICE_URL}"
        }), 503
    except requests.exceptions.Timeout:
        print("[ERROR] Recipe Service request timeout")
        return jsonify({
            "error": "Recipe Service timeout",
            "msg": "Request took too long"
        }), 504
    except Exception as e:
        print(f"[ERROR] Proxy error: {str(e)}")
        return jsonify({
            "error": "Proxy error",
            "msg": str(e)
        }), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"msg": "ไม่รู้จัก Route ที่เรียกใช้นะจ๊ะ", "code": 404}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"msg": "Internal Server Error", "code": 500}), 500

if __name__ == '__main__':
    print(f"[INFO] Starting Frontend Service...")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
