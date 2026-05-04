import os
import subprocess
import requests
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def generate_scene_video(scene, output_path):
    visual = scene.get('visual', 'cinematic Nigerian scene')
    prompt = f"{visual}, cinematic Nigerian film, professional cinematography, dramatic lighting, 4K, realistic"
    token = os.environ.get('HUGGINGFACE_TOKEN')

    if token:
        try:
            resp = requests.post(
                "https://api-inference.huggingface.co/models/damo-vilab/text-to-video-ms-1.7b",
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": prompt},
                timeout=120
            )
            if resp.status_code == 200 and 'video' in resp.headers.get('content-type', ''):
                with open(output_path, 'wb') as f:
                    f.write(resp.content)
                return {'success': True, 'path': output_path}
        except Exception as e:
            print(f"HF error: {e}")

    return generate_placeholder(scene, output_path)

def generate_placeholder(scene, output_path):
    colors = {
        'dramatic': '0x1a0a00', 'tense': '0x0a0000', 'ethereal': '0x0a0a2e',
        'romantic': '0x2e0a1a', 'triumphant': '0x002e0a', 'mysterious': '0x0a002e'
    }
    mood = scene.get('mood', 'dramatic').lower().replace('mood:', '').strip()
    color = colors.get(mood, '0x1a1a1a')
    title = scene.get('title', 'Scene').replace("'", "")[:30]
    try:
        result = subprocess.run([
            FFMPEG, '-y', '-f', 'lavfi',
            '-i', f'color=c={color}:size=1280x720:duration=12:rate=24',
            '-vf', f"drawtext=text='{title}':fontsize=32:fontcolor=gold:x=(w-text_w)/2:y=(h-text_h)/2",
            '-c:v', 'libx264', '-t', '12', output_path
        ], capture_output=True, timeout=30)
        if result.returncode == 0:
            return {'success': True, 'path': output_path, 'placeholder': True}
    except Exception as e:
        print(f"FFmpeg error: {e}")
    return {'success': False, 'error': 'Generation failed'}
