from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path
from dotenv import load_dotenv
import httpx
import json

load_dotenv()

app = FastAPI()

# ตั้งค่า Recipe Service URL (สำหรับ local development หรือ Docker)
RECIPE_SERVICE_URL = os.getenv('RECIPE_SERVICE_URL', 'http://localhost:5001')

print(f"[INFO] Starting Frontend Service...")
print(f"[INFO] Recipe Service URL: {RECIPE_SERVICE_URL}")

# เพิ่ม CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ตำแหน่ง templates
TEMPLATES_DIR = Path(__file__).parent / "templates"

@app.get("/")
async def index():
    """หน้าแรก"""
    return FileResponse(TEMPLATES_DIR / "index.html", media_type="text/html")

@app.get("/user-input")
async def user_input_page():
    """หน้ากรอกวัตถุดิบ"""
    return FileResponse(TEMPLATES_DIR / "userInput.html", media_type="text/html")

@app.get("/result")
async def result_page():
    """หน้าแสดงผล"""
    return FileResponse(TEMPLATES_DIR / "result.html", media_type="text/html")

@app.get("/api/config")
async def get_config():
    """ส่ง Recipe Service URL ให้ frontend เรียกตรง (ไม่ผ่าน proxy)"""
    return {"recipe_service_url": RECIPE_SERVICE_URL}

@app.post("/api/recommend")
async def proxy_recommend(body: dict):
    """Proxy endpoint ที่ forward request ไป recipe-service"""
    try:
        print(f"[INFO] Proxying request to {RECIPE_SERVICE_URL}/api/recommend")
        print(f"[INFO] Request data: {body}")
        
        # Forward request ไป recipe-service ด้วย httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f'{RECIPE_SERVICE_URL}/api/recommend',
                json=body,
                headers={'Content-Type': 'application/json'},
                timeout=60.0
            )
        
        print(f"[INFO] Recipe Service Response Status: {response.status_code}")
        
        # Return response จาก recipe-service ไป client
        return JSONResponse(
            status_code=response.status_code,
            content=response.json()
        )
        
    except httpx.ConnectError:
        print(f"[ERROR] ไม่สามารถเชื่อมต่อ Recipe Service ที่ {RECIPE_SERVICE_URL}")
        return JSONResponse(
            status_code=503,
            content={
                "error": "ไม่สามารถเชื่อมต่อ Recipe Service",
                "msg": f"Recipe Service unavailable at {RECIPE_SERVICE_URL}"
            }
        )
    except httpx.TimeoutException:
        print("[ERROR] Recipe Service request timeout")
        return JSONResponse(
            status_code=504,
            content={
                "error": "Recipe Service timeout",
                "msg": "Request took too long"
            }
        )
    except Exception as e:
        print(f"[ERROR] Proxy error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Proxy error",
                "msg": str(e)
            }
        )

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "frontend"}

if __name__ == '__main__':
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    print(f"[INFO] Starting Frontend Service on port {port}...")
    uvicorn.run(app, host='0.0.0.0', port=port)
