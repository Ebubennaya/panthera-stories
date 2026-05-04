import os
import subprocess
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def is_valid_video(path):
    if not path or not os.path.exists(path):
        return False
    if os.path.getsize(path) < 1000:
        return False
    result = subprocess.run(
        [FFMPEG, '-v', 'error', '-i', path, '-f', 'null', '-'],
        capture_output=True, timeout=15
    )
    return result.returncode == 0

def normalize_clip(input_path, output_path):
    result = subprocess.run([
        FFMPEG, '-y', '-i', input_path,
        '-c:v', 'libx264', '-preset', 'fast',
        '-r', '24', '-s', '1280x720',
        '-c:a', 'aac', '-ar', '44100', '-ac', '2',
        output_path
    ], capture_output=True, timeout=60)
    return result.returncode == 0

def assemble_video(scenes, output_path):
    approved = [s for s in scenes if s.get('status') == 'approved']

    valid = []
    for s in approved:
        path = s.get('video_path')
        if is_valid_video(path):
            valid.append(s)
        else:
            print(f"Skipping {s.get('id')} — file missing or invalid")

    if not valid:
        return {
            'success': False,
            'error': 'No valid video files found. Please go to Stage 3 and generate scenes first, then approve them in Stage 4.'
        }

    os.makedirs('/tmp/normalized', exist_ok=True)
    normalized_paths = []
    for s in valid:
        norm_path = f"/tmp/normalized/{s['id']}_norm.mp4"
        if normalize_clip(s['video_path'], norm_path):
            normalized_paths.append(norm_path)
        else:
            print(f"Could not normalize {s['id']}, skipping")

    if not normalized_paths:
        return {'success': False, 'error': 'All clips failed to normalize. Try regenerating scenes.'}

    concat_file = '/tmp/concat_list.txt'
    with open(concat_file, 'w') as f:
        for p in normalized_paths:
            f.write(f"file '{p}'\n")

    raw = output_path.replace('.mp4', '_raw.mp4')

    try:
        subprocess.run([
            FFMPEG, '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file, '-c', 'copy', raw
        ], capture_output=True, check=True, timeout=600)

        result = subprocess.run([
            FFMPEG, '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', raw
        ], capture_output=True, text=True)

        try:
            duration = float(result.stdout.strip())
        except:
            duration = 60.0

        fade_out = max(0, duration - 3)

        subprocess.run([
            FFMPEG, '-y', '-i', raw,
            '-vf', f'fade=t=in:st=0:d=2,fade=t=out:st={fade_out}:d=3',
            '-c:a', 'copy', output_path
        ], capture_output=True, check=True, timeout=600)

        if os.path.exists(raw):
            os.remove(raw)

        for p in normalized_paths:
            if os.path.exists(p):
                os.remove(p)

        return {'success': True, 'path': output_path, 'scenes_used': len(normalized_paths)}

    except subprocess.CalledProcessError as e:
        err = e.stderr.decode() if e.stderr else str(e)
        return {'success': False, 'error': f'Assembly failed: {err[:300]}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
