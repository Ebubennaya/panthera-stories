import os
import subprocess
import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def assemble_video(scenes, output_path):
    approved = [s for s in scenes if s.get('status') == 'approved' and s.get('video_path') and os.path.exists(s['video_path'])]
    if not approved:
        return {'success': False, 'error': 'No approved scenes with video files found'}

    concat_file = '/tmp/concat_list.txt'
    with open(concat_file, 'w') as f:
        for s in approved:
            f.write(f"file '{s['video_path']}'\n")

    raw = output_path.replace('.mp4', '_raw.mp4')

    try:
        subprocess.run([
            FFMPEG, '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_file, '-c', 'copy', raw
        ], capture_output=True, check=True, timeout=600)

        duration_result = subprocess.run([
            FFMPEG, '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', raw
        ], capture_output=True, text=True)

        try:
            duration = float(duration_result.stdout.strip())
        except:
            duration = 60.0

        fade_out_start = max(0, duration - 3)

        subprocess.run([
            FFMPEG, '-y', '-i', raw,
            '-vf', f'fade=t=in:st=0:d=2,fade=t=out:st={fade_out_start}:d=3',
            '-c:a', 'copy', output_path
        ], capture_output=True, check=True, timeout=600)

        if os.path.exists(raw):
            os.remove(raw)

        return {'success': True, 'path': output_path}

    except subprocess.CalledProcessError as e:
        return {'success': False, 'error': f'Assembly failed: {e.stderr.decode() if e.stderr else str(e)}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
