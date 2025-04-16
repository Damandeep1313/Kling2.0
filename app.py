import time
import jwt
import requests
from fastapi import FastAPI, Header, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

class VideoRequest(BaseModel):
    prompt: Optional[str] = "A sikh guy performing martial arts"
    duration: Optional[int] = 5
    resolution: Optional[str] = "720p"
    frame_rate: Optional[int] = 24
    style: Optional[str] = "cinematic"

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

def encode_jwt_token(ak, sk):
    headers = {
        "alg": "HS256",
        "typ": "JWT"
    }
    payload = {
        "iss": ak,
        "exp": int(time.time()) + 1800,
        "nbf": int(time.time()) - 5
    }
    print("🔐 Generating JWT token...")
    token = jwt.encode(payload, sk, algorithm="HS256", headers=headers)
    print(f"🔑 JWT token generated: {token}")
    return token

def generate_video(authorization, prompt="A sikh guy performing martial arts", duration=5, resolution="720p", frame_rate=24, style="cinematic"):
    url = "https://api.klingai.com/v1/videos/text2video"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {authorization}'
    }
    data = {
        "prompt": prompt,
        "duration": duration,
        "resolution": resolution,
        "frame_rate": frame_rate,
        "style": style
    }
    print(f"🎬 Sending video generation request with prompt: {prompt}, duration: {duration}, resolution: {resolution}, frame_rate: {frame_rate}, style: {style}")
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 200:
        task_id = response.json()['data']['task_id']
        print(f"🎬 Video generation task submitted. Task ID: {task_id}")
        return task_id
    else:
        print(f"❌ Error generating video: {response.text}")
        return None

def wait_for_video_url(authorization, task_id, check_interval=5):
    url = f"https://api.klingai.com/v1/videos/text2video/{task_id}"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {authorization}'
    }

    print(f"⏳ Waiting for video generation to complete. Checking every {check_interval} seconds...")
    while True:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()['data']
            status = data['task_status']
            print(f"⏳ Task status: {status}")

            if status in ["succeed", "completed"]:
                videos = data.get("task_result", {}).get("videos", [])
                if videos and videos[0].get("url"):
                    video_url = videos[0]["url"]
                    print(f"\n✅ Video is ready!\n🎥 Watch/download: {video_url}\n")
                    return video_url
                else:
                    print("🟡 Video is marked ready, but URL not provided yet. Retrying...")
            else:
                print(f"⏳ Task status: {status}. Waiting...")
        else:
            print(f"❌ Error checking status: {response.text}")

        time.sleep(check_interval)

@app.post("/generate_video")
async def generate_video_request(
    body: VideoRequest,
    x_api_key_ak: str = Header(..., alias="X-API-KEY-AK"),
    x_api_key_sk: str = Header(..., alias="X-API-KEY-SK")
):
    try:
        print("🔄 Request received to generate video...")
        print("✅ API keys extracted from request headers.")

        print(f"🔐 Generating JWT token with AK: {x_api_key_ak} and SK: {x_api_key_sk}")
        authorization = encode_jwt_token(x_api_key_ak, x_api_key_sk)

        print(f"🎬 Submitting video generation task...")
        task_id = generate_video(authorization, body.prompt, body.duration, body.resolution, body.frame_rate, body.style)

        if task_id:
            print(f"⏳ Waiting for video to be ready...")
            video_url = wait_for_video_url(authorization, task_id)
            return {"message": "Video generation complete", "video_url": video_url}
        else:
            return JSONResponse(status_code=500, content={"error": "Failed to generate video task."})

    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return JSONResponse(status_code=400, content={"error": str(e)})
