import os
import subprocess
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def is_valid(path):
    if not path or not os.path.exists(path) or os.path.getsize(path) < 500:
        return False
    r = subprocess.run([FFMPEG,'-v','error','-i',path,'-f','null','-'],
                       capture_output=True, timeout=15)
    return r.returncode == 0

def normalize(src, dst):
    r = subprocess.run([
        FFMPEG,'-y','-i',src,
        '-c:v','libx264','-preset','fast',
        '-r','24','-s','1280x720',
        '-c:a','aac','-ar','44100','-ac','2',
        dst
    ], capture_output=True, timeout=60)
    return r.returncode == 0

def assemble_video(scenes, output_path):
    approved = [s for s in scenes if s.get('status') == 'approved']
    valid = [s for s in approved if is_valid(s.get('video_path'))]

    if not valid:
        return {'success': False, 'error': 'No valid video files found. Generate and approve scenes in Stages 3 and 4 first.'}

    os.makedirs('/tmp/norm', exist_ok=True)
    norm_paths = []
    for s in valid:
        dst = f"/tmp/norm/{s['id']}.mp4"
        if normalize(s['video_path'], dst):
            norm_paths.append(dst)

    if not norm_paths:
        return {'success': False, 'error': 'Failed to normalize clips. Try regenerating scenes.'}

    concat = '/tmp/concat.txt'
    with open(concat, 'w') as f:
        for p in norm_paths:
            f.write(f"file '{p}'\n")

    raw = output_path.replace('.mp4', '_raw.mp4')
    try:
        subprocess.run([FFMPEG,'-y','-f','concat','-safe','0',
                        '-i',concat,'-c','copy',raw],
                       capture_output=True, check=True, timeout=600)

        probe = subprocess.run([FFMPEG,'-v','error','-show_entries','format=duration',
                                '-of','default=noprint_wrappers=1:nokey=1',raw],
                               capture_output=True, text=True)
        try:
            dur = float(probe.stdout.strip())
        except:
            dur = 60.0

        fade = max(0, dur - 3)
        subprocess.run([FFMPEG,'-y','-i',raw,
                        '-vf',f'fade=t=in:st=0:d=2,fade=t=out:st={fade}:d=3',
                        '-c:a','copy', output_path],
                       capture_output=True, check=True, timeout=600)

        if os.path.exists(raw):
            os.remove(raw)
        for p in norm_paths:
            if os.path.exists(p):
                os.remove(p)

        return {'success': True, 'path': output_path, 'scenes_used': len(norm_paths)}

    except subprocess.CalledProcessError as e:
        err = (e.stderr.decode() if e.stderr else str(e))[:300]
        return {'success': False, 'error': f'Assembly failed: {err}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
