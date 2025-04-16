import time
import jwt
import requests
from flask import Flask, request, jsonify

@app.route('/')
def home():
    return "Hello, World!"

app = Flask(__name__)

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
        print(f"❌ Error generating video: {response.json()}")
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
                    return True
                else:
                    print("🟡 Video is marked ready, but URL not provided yet. Retrying...")
            else:
                print(f"⏳ Task status: {status}. Waiting...")
        else:
            print(f"❌ Error checking status: {response.text}")

        time.sleep(check_interval)

@app.route('/generate_video', methods=['POST'])
def generate_video_request():
    try:
        print("🔄 Request received to generate video...")
        # Extracting ak and sk from separate headers
        ak = request.headers.get('X-API-KEY-AK')
        sk = request.headers.get('X-API-KEY-SK')

        if not ak or not sk:
            raise ValueError("Missing API keys in headers.")
        print("✅ API keys extracted from request headers.")

        # Extracting video parameters from the request body
        data = request.json
        prompt = data.get('prompt', "A sikh guy performing martial arts")
        duration = data.get('duration', 5)
        resolution = data.get('resolution', "720p")
        frame_rate = data.get('frame_rate', 24)
        style = data.get('style', "cinematic")

        print(f"🔐 Generating JWT token with AK: {ak} and SK: {sk}")
        authorization = encode_jwt_token(ak, sk)

        print(f"🎬 Submitting video generation task...")
        task_id = generate_video(authorization, prompt, duration, resolution, frame_rate, style)
        if task_id:
            print(f"⏳ Waiting for video to be ready...")
            wait_for_video_url(authorization, task_id)

        return jsonify({"message": "Video generation task started"}), 200
    except Exception as e:
        print(f"❌ Error occurred: {e}")
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    print("🟢 Starting Flask app...")
    app.run(debug=True)
