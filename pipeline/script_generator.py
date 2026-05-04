import os
import time
import random
from groq import Groq

NIGERIAN_NAMES = [
    'Adaeze','Chiamaka','Ngozi','Yetunde','Amara','Chisom','Teniola','Nneka','Zainab','Hauwa',
    'Emeka','Chukwudi','Olumide','Taiwo','Ifeanyi','Obinna','Babatunde','Seun','Ahmed','Kelechi',
    'Folake','Sade','Blessing','Aisha','Fatima','Femi','Ayo','Musa','Ibrahim','Chibuike'
]

LOCATIONS = [
    'Victoria Island glass tower','Lekki Phase 1 estate','Surulere back streets',
    'Eko Atlantic waterfront','Abuja Maitama district','Enugu coal camp','Calabar waterside',
    'Kano old city walls','Port Harcourt oil district','Lagos Island bridge market',
    'Onitsha main market','Ibadan University campus','Benin royal palace grounds',
    'Balogun market maze','Ikoyi colonial mansion'
]

TWISTS = [
    'the villain is revealed to be protecting a dying child',
    'the hero unknowingly caused the very problem they are solving',
    'a trusted ally is exposed as a spy working for the enemy',
    'the ancient prophecy was deliberately mistranslated for centuries',
    'a character believed dead walks in at the most critical moment',
    'the prize they fought for turns out to be worthless — the real treasure was something else',
    'two enemies discover they share the same bloodline',
    'the final betrayal comes from the person the audience trusted most'
]

STORY_BLUEPRINTS = {
    'folklore': [
        {
            'type': 'A powerful female priestess discovers a generational curse she herself must break — even if it kills her',
            'setting': 'Sacred forest kingdom with rivers, spirit realms, and ancient shrines',
            'conflict': 'Personal love vs sacred duty to her people',
            'tone': 'Epic, mythological, deeply emotional'
        },
        {
            'type': 'A hunted young man with forbidden ancestral powers discovers his true identity changes everything — including who his enemies are',
            'setting': 'Coastal fishing village being swallowed by a modern city',
            'conflict': 'Identity, survival, and the weight of a destiny he never chose',
            'tone': 'Dark supernatural thriller, fast-paced mystery'
        },
        {
            'type': 'An aging keeper of forbidden knowledge must choose one unlikely successor before dark forces destroy their entire lineage',
            'setting': 'Underground cave networks beneath a royal marketplace',
            'conflict': 'Legacy vs survival — what knowledge is worth dying to protect',
            'tone': 'Philosophical, tense, bittersweet ending'
        }
    ],
    'office': [
        {
            'type': 'A sharp junior analyst discovers her CEO has been laundering billions and must expose him before he erases her',
            'setting': 'Glass-tower corporate headquarters in Lagos Island',
            'conflict': 'Integrity vs career vs personal safety',
            'tone': 'Corporate thriller, paranoid tension, fast-paced'
        },
        {
            'type': 'Two rival executives secretly in love compete to destroy each other for the CEO position and only one can walk away',
            'setting': 'Government-linked construction empire in Abuja',
            'conflict': 'Ambition vs love — when winning means losing everything',
            'tone': 'Dramatic, romantic, morally complex'
        },
        {
            'type': 'A newly hired HR manager brought in to fix a toxic company slowly realises the rot starts at the very board that hired her',
            'setting': 'Nigerian subsidiary of a collapsing multinational bank',
            'conflict': 'Ethics vs institutional power — one woman vs an entire system',
            'tone': 'Intelligent, satirical, slow-burn suspense'
        }
    ],
    'corporate': [
        {
            'type': 'A whistleblower inside Nigeria largest oil company must release documents that will shake the entire government or stay silent forever',
            'setting': 'Port Harcourt oil company headquarters and Abuja corridors of power',
            'conflict': 'Truth vs survival in a country where truth gets people killed',
            'tone': 'Political thriller, urgent, high-stakes'
        },
        {
            'type': 'A self-made billionaire empire begins crumbling when his long-lost daughter returns and she knows exactly what he buried to get rich',
            'setting': 'Lagos penthouse boardrooms and village flashbacks',
            'conflict': 'Family, guilt, legacy, and the price of dirty money',
            'tone': 'Dynasty drama, emotional, explosive reveals'
        },
        {
            'type': 'Three business partners who built a company together are torn apart when one secretly sells their life work to a foreign conglomerate',
            'setting': 'Yaba tech hub and London boardroom negotiations',
            'conflict': 'Friendship, betrayal, and what success really costs',
            'tone': 'Modern drama, tense, bittersweet'
        }
    ],
    'romance': [
        {
            'type': 'A fiercely independent Lagos architect falls for the traditional man hired to demolish the historic building she is trying to save',
            'setting': 'Historic Lagos Island building under threat of demolition',
            'conflict': 'Love vs ambition — can two opposite worlds build something together',
            'tone': 'Warm, witty, emotionally rich'
        },
        {
            'type': 'Two strangers discover they have been secretly set up by their late grandmothers through letters written 40 years ago',
            'setting': 'Enugu family home, Lagos markets, Abuja rooftop restaurants',
            'conflict': 'Grief, destiny, trusting love when life has already broken you',
            'tone': 'Tender, healing, quietly beautiful'
        },
        {
            'type': 'A successful Abuja woman returns home for her sister wedding and falls for the one man her family will never accept',
            'setting': 'Delta State village wedding, Lagos flashbacks, family compound',
            'conflict': 'Family loyalty vs personal happiness vs class and tribe expectations',
            'tone': 'Dramatic, culturally rich, funny and painful in equal measure'
        }
    ],
    'action': [
        {
            'type': 'A retired military operative is pulled back in when her teenage son is kidnapped by the same cartel she dismantled ten years ago',
            'setting': 'Lagos slums, expressway chases, Apapa port warehouses',
            'conflict': 'A mother love vs a soldier code — and the line she swore she would never cross again',
            'tone': 'High-octane, emotional, relentless'
        },
        {
            'type': 'A street-smart Lagos fixer hired to recover a stolen hard drive discovers it contains evidence that could bring down the entire government',
            'setting': 'Lagos underground, Eko Bridge, Abuja safe houses, airport chase',
            'conflict': 'Self-preservation vs doing the right thing when everyone wants you dead',
            'tone': 'Fast, sharp, morally grey, wildly entertaining'
        },
        {
            'type': 'Two rival gang leaders who have been at war for a decade discover they were both manipulated by the same corrupt police chief',
            'setting': 'Oshodi, Mushin, Lagos waterways, police precinct siege',
            'conflict': 'Enemy of my enemy — can two killers trust each other long enough to survive',
            'tone': 'Gritty, tense, unexpected brotherhood'
        }
    ]
}

def generate_scripts(genre='folklore', research_themes=None):
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        return {'error': 'Groq API key not configured', 'scripts': []}

    client = Groq(api_key=api_key)
    blueprints = STORY_BLUEPRINTS.get(genre, STORY_BLUEPRINTS['folklore'])
    themes = ', '.join(research_themes) if research_themes else 'Nigerian storytelling'
    scripts = []

    for i in range(3):
        if i > 0:
            time.sleep(25)

        letter = ['A', 'B', 'C'][i]
        blueprint = blueprints[i]
        name1 = random.choice(NIGERIAN_NAMES)
        name2 = random.choice([n for n in NIGERIAN_NAMES if n != name1])
        location = random.choice(LOCATIONS)
        twist = random.choice(TWISTS)

        prompt = f"""You are a professional Nigerian screenwriter. Write SCRIPT OPTION {letter}.

MANDATORY STORY BLUEPRINT:
Story: {blueprint['type']}
Setting: {blueprint['setting']}
Conflict: {blueprint['conflict']}
Tone: {blueprint['tone']}

MANDATORY UNIQUE ELEMENTS:
- Lead character: {name1}
- Supporting character: {name2}
- Key location: {location}
- Final act twist: {twist}
- Trending themes to weave in: {themes}

OUTPUT — start with:
TITLE: Film Title
LOGLINE: One sentence pitch

Then EXACTLY 40 scenes, one per line:
SCENE_01|Scene Title|Camera description max 20 words|Spoken narration max 30 words|mood

Numbered SCENE_01 to SCENE_40. Nothing else."""

        for attempt in range(2):
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000,
                    temperature=0.9
                )
                scripts.append(parse_script(resp.choices[0].message.content, letter))
                break
            except Exception as e:
                if attempt == 0 and 'rate' in str(e).lower():
                    time.sleep(30)
                else:
                    scripts.append({
                        'option': letter, 'title': f'Option {letter}',
                        'logline': '', 'scenes': [], 'error': str(e), 'scene_count': 0
                    })
                    break

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
                    'visual': parts[2].strip().replace('Visual:', '').strip() if len(parts) > 2 else '',
                    'narration': parts[3].strip().replace('Narration:', '').strip() if len(parts) > 3 else '',
                    'mood': parts[4].strip() if len(parts) > 4 else 'dramatic',
                    'duration': 12,
                    'status': 'pending',
                    'video_path': None
                })
    return {
        'option': letter, 'title': title, 'logline': logline,
        'scenes': scenes, 'scene_count': len(scenes)
    }
