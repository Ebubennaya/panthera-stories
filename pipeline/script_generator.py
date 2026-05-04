import os
import time
from groq import Groq

GENRES = {
    'folklore': 'Ancient Nigerian folklore reimagined cinematically — Yoruba, Igbo or Hausa mythology, supernatural elements, traditional settings, epic storytelling',
    'office': 'Modern Nigerian corporate Lagos office drama — business ambition, workplace betrayal, professional characters, boardroom conflicts',
    'corporate': 'High-stakes Nigerian corporate thriller — executive power struggles, corruption, business empires, political connections',
    'romance': 'Modern Nigerian love story set in Lagos or Abuja — relatable characters, family pressure, modern relationships',
    'action': 'Nigerian action thriller — Lagos streets, high stakes, crime and justice, intense cinematic sequences'
}

def generate_scripts(genre='folklore', research_themes=None):
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return {'error': 'Groq API key not configured', 'scripts': []}

    client = Groq(api_key=api_key)
    genre_desc = GENRES.get(genre, GENRES['folklore'])
    themes = ', '.join(research_themes) if research_themes else 'Nigerian storytelling, drama, culture'
    scripts = []

    for i in range(3):
        if i > 0:
            time.sleep(65)

        letter = ['A', 'B', 'C'][i]
        prompt = f"""You are a professional Nigerian screenwriter. Write script option {letter}.

Genre: {genre_desc}
Trending themes: {themes}
Make this COMPLETELY DIFFERENT from options A and B — different story, different characters.

Write EXACTLY 15 scenes in this pipe-separated format (one scene per line):
SCENE_01|Scene Title|Visual description max 40 words|Narration max 30 words|dramatic

First two lines must be:
TITLE: Your Film Title Here
LOGLINE: One sentence story summary

Then 15 scenes. Output nothing else."""

        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.85
            )
            raw = resp.choices[0].message.content
            scripts.append(parse_script(raw, letter))
        except Exception as e:
            scripts.append({'option': letter, 'title': f'Option {letter}', 'logline': '', 'scenes': [], 'error': str(e)})

    return {'scripts': scripts}

def parse_script(text, letter):
    lines = text.strip().split('\n')
    title, logline, scenes = f'Script {letter}', '', []
    for line in lines:
        line = line.strip()
        if line.startswith('TITLE:'):
            title = line[6:].strip()
        elif line.startswith('LOGLINE:'):
            logline = line[8:].strip()
        elif line.startswith('SCENE_'):
            parts = line.split('|')
            if len(parts) >= 4:
                scenes.append({
                    'id': parts[0].strip(),
                    'title': parts[1].strip() if len(parts) > 1 else '',
                    'visual': parts[2].strip() if len(parts) > 2 else '',
                    'narration': parts[3].strip() if len(parts) > 3 else '',
                    'mood': parts[4].strip() if len(parts) > 4 else 'dramatic',
                    'duration': 8,
                    'status': 'pending',
                    'video_path': None
                })
    return {'option': letter, 'title': title, 'logline': logline, 'scenes': scenes, 'scene_count': len(scenes)}
