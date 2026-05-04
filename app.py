import os
import json
import threading
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'panthera-2024-secret')

STATE_FILE = '/tmp/panthera_state.json'
SCENES_DIR = '/tmp/scenes'
AUDIO_DIR = '/tmp/audio'
OUTPUT_DIR = '/tmp/output'

for d in [SCENES_DIR, AUDIO_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {
        'stage': 1, 'research': None, 'scripts': None,
        'selected_script': None, 'production_status': {},
        'script_status': 'idle', 'assembly_status': 'idle',
        'final_video': None, 'genre': 'folklore'
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

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
        'groq': bool(os.environ.get('GROQ_API_KEY')),
        'huggingface': bool(os.environ.get('HUGGINGFACE_TOKEN'))
    })

@app.route('/api/research', methods=['POST'])
def run_research():
    from pipeline.youtube_research import research_youtube
    try:
        results = research_youtube()
        state = load_state()
        state['research'] = results
        save_state(state)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/generate-scripts', methods=['POST'])
def run_generate_scripts():
    from pipeline.script_generator import generate_scripts
    data = request.json or {}
    genre = data.get('genre', 'folklore')
    state = load_state()
    themes = (state.get('research') or {}).get('themes', [])
    state['script_status'] = 'generating'
    state['genre'] = genre
    state['scripts'] = None
    save_state(state)

    def bg():
        try:
            result = generate_scripts(genre=genre, research_themes=themes)
            s = load_state()
            s['scripts'] = result.get('scripts', [])
            s['script_status'] = 'complete'
            save_state(s)
        except Exception as e:
            s = load_state()
            s['script_status'] = f'error: {str(e)}'
            save_state(s)

    threading.Thread(target=bg, daemon=True).start()
    return jsonify({'success': True, 'message': 'Generating 3 scripts — takes 3-4 minutes due to rate limits.'})

@app.route('/api/script-status')
def script_status():
    state = load_state()
    return jsonify({'status': state.get('script_status', 'idle'), 'scripts': state.get('scripts', [])})

@app.route('/api/select-script', methods=['POST'])
def select_script():
    data = request.json or {}
    idx = data.get('index', 0)
    state = load_state()
    scripts = state.get('scripts') or []
    if idx >= len(scripts):
        return jsonify({'success': False, 'error': 'Invalid script index'})
    selected = scripts[idx]
    state['selected_script'] = selected
    state['stage'] = 3
    state['production_status'] = {s['id']: 'pending' for s in selected.get('scenes', [])}
    save_state(state)
    return jsonify({'success': True, 'script': selected})

@app.route('/api/generate-scene', methods=['POST'])
def generate_scene():
    from pipeline.video_generator import generate_scene_video
    data = request.json or {}
    scene_id = data.get('scene_id')
    state = load_state()
    scenes = (state.get('selected_script') or {}).get('scenes', [])
    scene = next((s for s in scenes if s['id'] == scene_id), None)
    if not scene:
        return jsonify({'success': False, 'error': 'Scene not found'})

    output_path = os.path.join(SCENES_DIR, f"{scene_id}.mp4")
    state['production_status'][scene_id] = 'generating'
    save_state(state)

    def bg():
        result = generate_scene_video(scene, output_path)
        s = load_state()
        if result.get('success'):
            s['production_status'][scene_id] = 'generated'
            for sc in s['selected_script']['scenes']:
                if sc['id'] == scene_id:
                    sc['video_path'] = output_path
        else:
            s['production_status'][scene_id] = 'failed'
        save_state(s)

    threading.Thread(target=bg, daemon=True).start()
    return jsonify({'success': True})

@app.route('/api/scene-status')
def scene_status():
    state = load_state()
    return jsonify({'production_status': state.get('production_status', {})})

@app.route('/api/approve-scene', methods=['POST'])
def approve_scene():
    data = request.json or {}
    scene_id = data.get('scene_id')
    action = data.get('action', 'approve')
    state = load_state()
    if scene_id:
        state['production_status'][scene_id] = 'approved' if action == 'approve' else 'pending'
        if action == 'approve':
            for sc in (state.get('selected_script') or {}).get('scenes', []):
                if sc['id'] == scene_id:
                    sc['status'] = 'approved'
    save_state(state)
    return jsonify({'success': True})

@app.route('/api/assemble', methods=['POST'])
def run_assemble():
    from pipeline.video_assembler import assemble_video
    state = load_state()
    scenes = (state.get('selected_script') or {}).get('scenes', [])
    output_path = os.path.join(OUTPUT_DIR, 'panthera_final.mp4')
    state['assembly_status'] = 'assembling'
    save_state(state)

    def bg():
        result = assemble_video(scenes, output_path)
        s = load_state()
        if result.get('success'):
            s['final_video'] = output_path
            s['assembly_status'] = 'complete'
        else:
            s['assembly_status'] = f"error: {result.get('error', 'Unknown error')}"
        save_state(s)

    threading.Thread(target=bg, daemon=True).start()
    return jsonify({'success': True, 'message': 'Assembly started'})

@app.route('/api/assembly-status')
def assembly_status():
    state = load_state()
    return jsonify({'status': state.get('assembly_status', 'idle'), 'has_video': bool(state.get('final_video'))})

@app.route('/api/download')
def download_video():
    state = load_state()
    path = state.get('final_video')
    if path and os.path.exists(path):
        return send_file(path, as_attachment=True, download_name='panthera_stories_film.mp4')
    return jsonify({'error': 'No video ready'}), 404

@app.route('/api/reset', methods=['POST'])
def reset_app():
    if os.path.exists(STATE_FILE):
        os.remove(STATE_FILE)
    return jsonify({'success': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
