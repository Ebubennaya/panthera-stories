import os
import subprocess
import shutil
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def generate_scene_video(scene, output_path):
    visual = scene.get('visual', 'cinematic Nigerian scene')
    mood = scene.get('mood', 'dramatic')
    prompt = (f"{visual}, cinematic Nigerian film, professional cinematography, "
              f"{mood} atmosphere, realistic people with natural movement, high quality 4K")
    token = os.environ.get('HUGGINGFACE_TOKEN')

    if token:
        # Try Wan2.1 — best free motion video
        result = _try_wan2(prompt, output_path, token)
        if result:
            return {'success': True, 'path': output_path}

    # Fallback: animated placeholder
    return _placeholder(scene, output_path)

def _try_wan2(prompt, output_path, token):
    try:
        from gradio_client import Client  # lazy import — only loads when called
        client = Client("Wan-AI/Wan2.1-T2V-14B", hf_token=token)
        result = client.predict(
            prompt=prompt,
            negative_prompt="blurry, static, low quality, no motion, cartoon, watermark",
            num_inference_steps=20,
            guidance_scale=7.0,
            api_name="/generate"
        )
        if result and os.path.exists(str(result)):
            shutil.copy(str(result), output_path)
            return True
    except Exception as e:
        print(f"Wan2.1 error: {e}")
    return False

def _placeholder(scene, output_path):
    colors = {
        'dramatic':'0x1a0a00','tense':'0x0a0000','ethereal':'0x0a0a2e',
        'romantic':'0x2e0a1a','triumphant':'0x002e0a','mysterious':'0x0a002e'
    }
    mood = scene.get('mood','dramatic').lower().replace('mood:','').strip()
    color = colors.get(mood, '0x111111')
    title = scene.get('title','Scene').replace("'",'').replace('"','')[:28]
    narr = scene.get('narration','').replace("'",'').replace('"','')[:60]
    try:
        result = subprocess.run([
            FFMPEG, '-y', '-f', 'lavfi',
            '-i', f'color=c={color}:size=1280x720:duration=12:rate=24',
            '-vf', (f"drawtext=text='{title}':fontsize=34:fontcolor=gold:"
                   f"x=(w-text_w)/2:y=(h-text_h)/2-30,"
                   f"drawtext=text='{narr}':fontsize=18:fontcolor=white:"
                   f"x=(w-text_w)/2:y=(h-text_h)/2+30"),
            '-c:v', 'libx264', '-t', '12', output_path
        ], capture_output=True, timeout=30)
        if result.returncode == 0:
            return {'success': True, 'path': output_path, 'placeholder': True}
    except Exception as e:
        print(f"Placeholder error: {e}")
    return {'success': False, 'error': 'Generation failed'}
