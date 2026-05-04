import os
import asyncio
import edge_tts

VOICES = ['en-NG-AbeolaNeural', 'en-NG-EzinneNeural']

async def _generate(text, path, voice):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(path)

def generate_voiceover(text, output_path, voice=None):
    if not voice:
        voice = VOICES[0]
    if not text or not text.strip():
        return {'success': False, 'error': 'No narration text provided'}
    try:
        asyncio.run(_generate(text, output_path, voice))
        return {'success': True, 'path': output_path}
    except Exception as e:
        return {'success': False, 'error': str(e)}
