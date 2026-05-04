import os
import subprocess
import shutil

def generate_scene_video(scene, output_path):
    visual = scene.get('visual', 'cinematic Nigerian scene')
    mood = scene.get('mood', 'dramatic')
    prompt = f"{visual}, cinematic Nigerian film, professional cinematography, dramatic lighting, 4K, realistic"

    try:
        from gradio_client import Client
        token = os.environ.get('HUGGINGFACE_TOKEN')
        client = Client("Wan-AI/Wan2.1-T2V-14B", hf_token=token)
        result = client.predict(
            prompt=prompt,
            negative_prompt="blurry, low quality, cartoon, text, watermark",
            num_inference_steps=20,
            guidance_scale=7.0,
            api_name="/generate"
        )
        if result and os.path.exists(str(result)):
            shutil.copy(str(result), output_path)
            return {'success': True, 'path': output_path}
    except Exception as e:
        print(f"HuggingFace error: {e}")

    return generate_placeholder(scene, output_path, mood)

def generate_placeholder(scene, output_path, mood):
    colors = {
        'dramatic': '0x1a0a00', 'tense': '0x0a0000', 'ethereal': '0x0a0a2e',
        'romantic': '0x2e0a1a', 'triumphant': '0x002e0a', 'mysterious': '0x0a002e'
    }
    mood_key = mood.lower().replace('mood:', '').strip()
    color = colors.get(mood_key, '0x1a1a1a')
    title = scene.get('title', 'Scene').replace("'", "")[:30]

    try:
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c={color}:size=1280x720:duration=8:rate=24',
            '-vf', f"drawtext=text='{title}':fontsize=32:fontcolor=gold:x=(w-text_w)/2:y=(h-text_h)/2",
            '-c:v', 'libx264', '-t', '8',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        if result.returncode == 0:
            return {'success': True, 'path': output_path, 'placeholder': True}
    except Exception as e:
        print(f"FFmpeg error: {e}")

    return {'success': False, 'error': 'Video generation failed'}
