import os
import re
import json
import threading
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'panthera-2024-secret')

STATE_FILE = '/tmp/panthera_state.json'
SCENES_DIR = '/tmp/scenes'
OUTPUT_DIR = '/tmp/output'

for d in [SCENES_DIR, '/tmp/audio', OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {'stage':1,'research':None,'scripts':None,'selected_script':None,
            'production_status':{},'script_status':'idle','assembly_status':'idle',
            'final_video':None,'genre':'folklore'}

def save_state(s):
    with open(STATE_FILE,'w') as f:
        json.dump(s, f)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/state')
def get_state():
    return jsonify(load_state())

@app.route('/api/keys')
def check_keys():
    return jsonify({
        'youtube': bool(os.environ.get('YOUTUBE_API_KEY')),
        'groq':    bool(os.environ.get('GROQ_API_KEY')),
        'huggingface': bool(os.environ.get('HUGGINGFACE_TOKEN'))
    })

@app.route('/api/research', methods=['POST'])
def run_research():
    from pipeline.youtube_research import research_youtube
    try:
        results = research_youtube()
        s = load_state(); s['research'] = results; save_state(s)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-scripts', methods=['POST'])
def run_generate_scripts():
    from pipeline.script_generator import generate_scripts
    data = request.json or {}
    genre = data.get('genre', 'folklore')
    s = load_state()
    themes = (s.get('research') or {}).get('themes', [])
    s['script_status'] = 'generating'; s['scripts'] = None; s['genre'] = genre
    save_state(s)
    def bg():
        try:
            res = generate_scripts(genre=genre, research_themes=themes)
            st = load_state(); st['scripts'] = res.get('scripts',[]); st['script_status'] = 'complete'; save_state(st)
        except Exception as e:
            st = load_state(); st['script_status'] = f'error: {e}'; save_state(st)
    threading.Thread(target=bg, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/script-status')
def script_status():
    s = load_state()
    return jsonify({'status': s.get('script_status','idle'), 'scripts': s.get('scripts',[])})

@app.route('/api/select-script', methods=['POST'])
def select_script():
    data = request.json or {}
    idx = data.get('index', 0)
    s = load_state()
    scripts = s.get('scripts') or []
    if idx >= len(scripts):
        return jsonify({'success': False, 'error': 'Invalid index'})
    sel = scripts[idx]
    s['selected_script'] = sel
    s['production_status'] = {sc['id']:'pending' for sc in sel.get('scenes',[])}
    save_state(s)
    return jsonify({'success': True, 'script': sel})

@app.route('/api/generate-scene', methods=['POST'])
def generate_scene():
    from pipeline.video_generator import generate_scene_video
    data = request.json or {}
    scene_id = data.get('scene_id')
    s = load_state()
    scenes = (s.get('selected_script') or {}).get('scenes', [])
    scene = next((sc for sc in scenes if sc['id'] == scene_id), None)
    if not scene:
        return jsonify({'success': False, 'error': 'Scene not found'})
    out = os.path.join(SCENES_DIR, f"{scene_id}.mp4")
    s['production_status'][scene_id] = 'generating'; save_state(s)
    def bg():
        res = generate_scene_video(scene, out)
        st = load_state()
        if res.get('success'):
            st['production_status'][scene_id] = 'generated'
            for sc in st['selected_script']['scenes']:
                if sc['id'] == scene_id:
                    sc['video_path'] = out
        else:
            st['production_status'][scene_id] = 'failed'
        save_state(st)
    threading.Thread(target=bg, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/scene-status')
def scene_status():
    s = load_state()
    return jsonify({'production_status': s.get('production_status', {})})

@app.route('/api/video/<scene_id>')
def serve_video(scene_id):
    if not re.match(r'^SCENE_\d+$', scene_id):
        return jsonify({'error': 'Invalid'}), 400
    path = os.path.join(SCENES_DIR, f"{scene_id}.mp4")
    if os.path.exists(path):
        return send_file(path, mimetype='video/mp4')
    return jsonify({'error': 'Not found'}), 404

@app.route('/api/approve-scene', methods=['POST'])
def approve_scene():
    data = request.json or {}
    scene_id = data.get('scene_id')
    action = data.get('action', 'approve')
    s = load_state()
    if scene_id:
        val = 'approved' if action == 'approve' else 'pending'
        s['production_status'][scene_id] = val
        for sc in (s.get('selected_script') or {}).get('scenes', []):
            if sc['id'] == scene_id:
                sc['status'] = val
    save_state(s)
    return jsonify({'success': True})

@app.route('/api/assemble', methods=['POST'])
def run_assemble():
    from pipeline.video_assembler import assemble_video
    s = load_state()
    scenes = (s.get('selected_script') or {}).get('scenes', [])
    out = os.path.join(OUTPUT_DIR, 'panthera_final.mp4')
    s['assembly_status'] = 'assembling'; save_state(s)
    def bg():
        res = assemble_video(scenes, out)
        st = load_state()
        st['final_video'] = out if res.get('success') else None
        st['assembly_status'] = 'complete' if res.get('success') else f"error: {res.get('error','')}"
        save_state(st)
    threading.Thread(target=bg, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/assembly-status')
def assembly_status():
    s = load_state()
    return jsonify({'status': s.get('assembly_status','idle'), 'has_video': bool(s.get('final_video'))})

@app.route('/api/download')
def download():
    s = load_state()
    p = s.get('final_video')
    if p and os.path.exists(p):
        return send_file(p, as_attachment=True, download_name='panthera_stories_film.mp4')
    return jsonify({'error': 'No video'}), 404

@app.route('/api/reset', methods=['POST'])
def reset():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
