const express = require('express');
const jwt = require('jsonwebtoken');
const axios = require('axios');
const bodyParser = require('body-parser');

const app = express();
app.use(bodyParser.json());

const PORT = process.env.PORT || 3000;

// Default response
app.get('/', (req, res) => {
  res.json({ message: 'Hello, World!' });
});

app.head('/', (req, res) => {
  res.status(200).send();
});

// JWT token generation
function encodeJwtToken(ak, sk) {
  const payload = {
    iss: ak,
    exp: Math.floor(Date.now() / 1000) + 1800,
    nbf: Math.floor(Date.now() / 1000) - 5,
  };

  const options = {
    algorithm: 'HS256',
    header: {
      alg: 'HS256',
      typ: 'JWT',
    },
  };

  console.log('🔐 Generating JWT token...');
  const token = jwt.sign(payload, sk, options);
  console.log(`🔑 JWT token generated: ${token}`);
  return token;
}

async function generateVideo(authorization, {
  prompt = 'A sikh guy performing martial arts',
  duration = 5,
  resolution = '720p',
  frame_rate = 24,
  style = 'cinematic',
}) {
  const url = 'https://api.klingai.com/v1/videos/text2video';
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${authorization}`,
  };

  const data = { prompt, duration, resolution, frame_rate, style };
  console.log('🎬 Sending video generation request:', data);

  try {
    const response = await axios.post(url, data, { headers });
    const taskId = response.data.data.task_id;
    console.log(`🎬 Task submitted. Task ID: ${taskId}`);
    return taskId;
  } catch (err) {
    console.error('❌ Error generating video:', err.response?.data || err.message);
    return null;
  }
}

async function waitForVideoUrl(authorization, taskId, checkInterval = 5000) {
  const url = `https://api.klingai.com/v1/videos/text2video/${taskId}`;
  const headers = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${authorization}`,
  };

  console.log(`⏳ Polling for video status every ${checkInterval / 1000}s...`);

  while (true) {
    try {
      const response = await axios.get(url, { headers });
      const data = response.data.data;
      const status = data.task_status;
      console.log(`⏳ Task status: ${status}`);

      if (['succeed', 'completed'].includes(status)) {
        const videoUrl = data.task_result?.videos?.[0]?.url;
        if (videoUrl) {
          console.log(`✅ Video ready! 🎥 ${videoUrl}`);
          return videoUrl;
        }
        console.log('🟡 Status ready but URL not yet available. Retrying...');
      }
    } catch (err) {
      console.error('❌ Error checking task status:', err.response?.data || err.message);
    }

    await new Promise((resolve) => setTimeout(resolve, checkInterval));
  }
}

// POST /generate_video endpoint
app.post('/generate_video', async (req, res) => {
  const body = req.body;
  const ak = req.header('X-API-KEY-AK');
  const sk = req.header('X-API-KEY-SK');

  if (!ak || !sk) {
    return res.status(400).json({ error: 'Missing API keys in headers' });
  }

  try {
    console.log('🔄 Video generation request received.');
    const token = encodeJwtToken(ak, sk);
    const taskId = await generateVideo(token, body);

    if (!taskId) {
      return res.status(500).json({ error: 'Failed to generate video task.' });
    }

    const videoUrl = await waitForVideoUrl(token, taskId);
    return res.json({ message: 'Video generation complete', video_url: videoUrl });
  } catch (err) {
    console.error('❌ Error occurred:', err);
    return res.status(400).json({ error: err.message });
  }
});

app.listen(PORT, () => {
  console.log(`🚀 Server is running on http://localhost:${PORT}`);
});
