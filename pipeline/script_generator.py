import os
import re
import json
import random
import time
from groq import Groq

STORY_BLUEPRINTS = {
    "folklore": [
        {"setup": "A village priestess carries a 200-year-old curse that activates when a stranger arrives bearing an ancient mask", "protagonist": "female priestess", "conflict": "break the curse before it consumes the village"},
        {"setup": "A young man discovers he is the last living descendant of a spirit-hunter clan, and the forest spirits want him dead before he remembers his power", "protagonist": "young male descendant", "conflict": "remember ancestral power before spirits destroy him"},
        {"setup": "An aging village elder must pass forbidden knowledge to an unworthy successor before a supernatural drought kills everyone", "protagonist": "aging elder", "conflict": "find a worthy successor among corrupted youth"},
    ],
    "office drama": [
        {"setup": "A junior financial analyst discovers the CEO has been laundering money through a charity fund and must expose the truth before being framed", "protagonist": "junior analyst", "conflict": "expose corruption without becoming the scapegoat"},
        {"setup": "Two rival department heads competing for the same VP position fall in love, creating an impossible conflict between ambition and heart", "protagonist": "female department head", "conflict": "choose career or love when both are at stake"},
        {"setup": "An HR manager discovers the board is secretly planning to fire 200 workers and must organize resistance using only internal company rules", "protagonist": "HR manager", "conflict": "protect workers using the system against itself"},
    ],
    "corporate": [
        {"setup": "A geologist at a major oil company discovers falsified environmental reports that will poison a river delta, risking career and life to go public", "protagonist": "female geologist", "conflict": "expose environmental crime while avoiding assassination"},
        {"setup": "A billionaire's daughter returns from abroad to find her father's empire built on land stolen from her mother's village", "protagonist": "returning daughter", "conflict": "dismantle father's empire or find a path to real justice"},
        {"setup": "Two business partners who built a tech startup from nothing discover their investor has been secretly stealing their IP to launch a competitor", "protagonist": "male co-founder", "conflict": "reclaim stolen intellectual property before the company collapses"},
    ],
    "romance": [
        {"setup": "An architect hired to design a luxury tower falls in love with the community organizer fighting to stop demolition of the neighborhood it will replace", "protagonist": "female architect", "conflict": "choose contract or conscience and the man fighting her work"},
        {"setup": "Two strangers discover their late grandmothers were lifelong lovers separated by a family feud, and must decide whether to honor or end the feud", "protagonist": "male grandson", "conflict": "honor a hidden love story or preserve family pride"},
        {"setup": "A woman promised in marriage to a wealthy chief secretly loves the village teacher, and the wedding is only three days away", "protagonist": "betrothed woman", "conflict": "escape an arranged marriage without destroying family honor"},
    ],
    "action": [
        {"setup": "A former soldier turned caterer discovers her teenage son has been recruited by a drug cartel and goes to war to get him back", "protagonist": "female former soldier", "conflict": "extract son from cartel without getting both of them killed"},
        {"setup": "A fixer who cleans up crimes for the elite finds a hard drive linking the president to political murders and must decide what to do with it", "protagonist": "male fixer", "conflict": "use evidence for justice or trade it for personal survival"},
        {"setup": "Two rival gang leaders must form an unlikely alliance when a corrupt police chief plans to frame both of them for a massacre", "protagonist": "female gang leader", "conflict": "trust the enemy to defeat the real threat"},
    ],
}

NIGERIAN_NAMES = ["Adaeze", "Chukwuemeka", "Funmilayo", "Babatunde", "Ngozi", "Emeka",
                  "Chioma", "Taiwo", "Amaka", "Seun", "Tobi", "Yetunde", "Ifeanyi", "Adeola"]
ALL_LOCATIONS = ["Lekki Phase 1", "Victoria Island", "Surulere", "Ikeja GRA", "Yaba",
                 "Awka Etiti", "Oyo town", "Badagry", "Calabar waterfront", "Arochukwu forest",
                 "Ile-Ife sacred grove", "Kano old city", "Benin Kingdom palace", "Owerri"]
PLOT_TWISTS = [
    "the antagonist is revealed to be the protagonist's long-lost sibling",
    "the hero discovers they have been manipulated from the very beginning",
    "a trusted ally switches sides at the worst possible moment",
    "the solution requires the hero to sacrifice what they love most",
    "everything the hero believed about their past is a carefully constructed lie",
]


def _get_blueprints(genre):
    key = genre.lower().strip()
    blueprints = STORY_BLUEPRINTS.get(key, STORY_BLUEPRINTS["folklore"])
    return random.sample(blueprints, min(3, len(blueprints)))


def generate_scripts(genre, progress_callback=None, research_themes=None):
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")

    client = Groq(api_key=api_key)

    names = random.sample(NIGERIAN_NAMES, 4)
    location = random.choice(ALL_LOCATIONS)
    twist = random.choice(PLOT_TWISTS)
    blueprints = _get_blueprints(genre)

    if progress_callback:
        progress_callback("Building 3 story blueprints...", 10)

    prompt = f"""You are a master Nigerian storyteller and Nollywood scriptwriter.

Genre: {genre}
Nigerian names to use across stories: {', '.join(names)}
Key Nigerian location: {location}
Mandatory plot twist to weave in (for at least one story): {twist}

Generate 3 COMPLETELY DIFFERENT scripts — different characters, different settings, different plots.

STORY A: {blueprints[0]['setup']}
Protagonist type: {blueprints[0]['protagonist']}
Core conflict: {blueprints[0]['conflict']}

STORY B: {blueprints[1]['setup']}
Protagonist type: {blueprints[1]['protagonist']}
Core conflict: {blueprints[1]['conflict']}

STORY C: {blueprints[2]['setup']}
Protagonist type: {blueprints[2]['protagonist']}
Core conflict: {blueprints[2]['conflict']}

Write exactly 25 scenes per script. Use this compact pipe-separated format (one scene per line):
SCENE_XX|Scene Title|Xs|What the camera sees (specific colors, textures, actions, Nigerian setting)|Words spoken by narrator (20-40 words)|mood|sound/music

Rules:
- Scenes 8-15 seconds each
- Visuals must be specific and physical — no abstract descriptions
- Each story must feel like a completely different film
- Strong opening hook on SCENE_01, emotional climax around SCENE_20, resolution by SCENE_25

Output exactly this structure:

=== SCRIPT A: [Unique Film Title] ===
LOGLINE: [One punchy sentence]
SCENE_01|...|...|...|...|...|...
SCENE_02|...|...|...|...|...|...
[continue to SCENE_25]

=== SCRIPT B: [Unique Film Title] ===
LOGLINE: [One punchy sentence]
SCENE_01|...|...|...|...|...|...
[continue to SCENE_25]

=== SCRIPT C: [Unique Film Title] ===
LOGLINE: [One punchy sentence]
SCENE_01|...|...|...|...|...|...
[continue to SCENE_25]"""

    if progress_callback:
        progress_callback("Generating all 3 scripts — single optimised call...", 25)

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=7000,
            )
            full_text = response.choices[0].message.content
            break
        except Exception as e:
            err = str(e).lower()
            if "rate_limit" in err and attempt == 0:
                if progress_callback:
                    progress_callback("Rate limit hit — waiting 35 seconds then retrying...", 25)
                time.sleep(35)
            else:
                raise

    if progress_callback:
        progress_callback("Parsing and saving scripts...", 85)

    scripts = _parse_scripts(full_text)

    os.makedirs(".tmp", exist_ok=True)
    summaries = {}
    for letter in ["A", "B", "C"]:
        content = scripts.get(letter, f"# Script {letter}\n\n(Generation incomplete — please regenerate)")
        with open(f".tmp/script_option_{letter}.md", "w", encoding="utf-8") as f:
            f.write(content)
        summaries[letter] = _extract_summary(content, letter)

    if progress_callback:
        progress_callback("All 3 scripts ready!", 100)

    return summaries


def _parse_scripts(text):
    scripts = {}
    parts = re.split(r'===\s*SCRIPT\s+([A-C]):', text, flags=re.IGNORECASE)
    # parts = [before_A, 'A', A_title+content, 'B', B_title+content, 'C', C_title+content]
    if len(parts) >= 7:
        for i, letter in enumerate(["A", "B", "C"]):
            section_raw = parts[i * 2 + 2]
            lines = section_raw.strip().split("\n")
            title = lines[0].strip().rstrip("=").strip() if lines else f"Story {letter}"
            body = "\n".join(lines[1:]).strip()
            scripts[letter] = f"# Script Option {letter}: {title}\n\n{body}"
    else:
        # Fallback: grab by SCRIPT X marker
        for letter in ["A", "B", "C"]:
            m = re.search(
                rf'SCRIPT\s+{letter}[:\s]+(.*?)(?=SCRIPT\s+[A-C]|$)',
                text, re.IGNORECASE | re.DOTALL
            )
            scripts[letter] = f"# Script Option {letter}\n\n{m.group(1).strip()}" if m else ""
    return scripts


def _extract_summary(script_text, letter):
    title, logline = f"Story {letter}", ""
    for line in script_text.split("\n")[:15]:
        if line.startswith("# Script Option"):
            parts = line.split(":", 1)
            if len(parts) > 1:
                title = parts[1].strip()
        elif line.upper().startswith("LOGLINE:"):
            logline = line.split(":", 1)[1].strip() if ":" in line else ""
    return {"title": title, "logline": logline}
