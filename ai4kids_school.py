"""
AI4Kids.pk — School v5  (5-Subject School Edition)
8 Subjects: AI, Robotics, English, Math, Science
Daily routine: Assembly -> Timetable -> 5 Periods
Admin dashboard + Student portal
Run:  streamlit run ai4kids_school.py
"""

import os, json, datetime, warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
from openai import OpenAI

# Hand-drawn SVG teaching visuals (fractions, shapes, ghadi, circuits...) — Rs 0
try:
    from topic_visuals import get_topic_visual, real_note_images, lesson_image_path
except Exception:                      # app must still run if the file is missing
    def get_topic_visual(subject_key, grade, topic_title):
        return None
    def real_note_images():
        return []
    def lesson_image_path(grade, subject_key, title):
        return None

def render_money_photos(topic_title):
    """Agar teacher ne asli note ki photos note_images/ mein rakhi hain to
    wohi dikhao — pehchan-ne ke liye asli tasveer sab se behtar hai."""
    t = (topic_title or "").lower()
    if not any(k in t for k in ("paisa", "paise", "money", "currency", "sikka")):
        return
    pics = real_note_images()
    if not pics:
        st.caption("💡 Teacher: asli note ki photo `note_images/` folder mein "
                   "rakhein (rs10.jpg, rs20.jpg, rs50.jpg, rs100.jpg, coins.jpg) — "
                   "phir yahan asli tasveer dikhegi.")
        st.link_button("🏦 State Bank — 'Rupay ko Pehchano' (asli note dekho)",
                       "https://www.sbp.org.pk/finance/Pak.asp",
                       width='stretch')
        return
    st.markdown("#### 📸 Asli note — pehchano")
    cols = st.columns(min(len(pics), 3))
    for i, (label, path) in enumerate(pics):
        with cols[i % len(cols)]:
            st.image(path, caption=label, width='stretch')

# ---- Inference endpoint: ai_config.json se aata hai (base_url + key + model) ----
# Endpoint badalne ke liye SIRF ai_config.json edit karein. Test: python check_ai_config.py
import ai_config

# ===========================================================================
# AI ON / OFF  —  "KB MODE"
# ---------------------------------------------------------------------------
# Agar API key set nahi hai to school CRASH nahi hota. Woh KB Mode mein
# chalta hai aur yeh sab kuch phir bhi kaam karta hai (Rs 0 kharcha):
#
#   * 150 tayyar sabaq (kb/grade_1..5)      * 150 tayyar quiz
#   * cached awaaz (tts_cache)              * hand-drawn SVG visuals
#   * assembly, hazri, sitare, streak       * homework diary, ghalti copy
#   * record room, report card              * lesson bank + curriculum
#
# Sirf yeh band rehta hai: naye (KB se bahar) sabaq/quiz, Admin ka AI chat,
# aur nayi awaaz. Public demo ke liye yeh sab se mehfooz tareeqa hai —
# koi API kharcha nahi ho sakta.
# ===========================================================================
try:
    client = ai_config.get_client()
    AI_ENABLED = True
    AI_OFF_REASON = ""
except Exception as _ai_err:
    client = None
    AI_ENABLED = False
    AI_OFF_REASON = str(_ai_err)

MODEL = ai_config.MODEL

AI_OFF_MESSAGE = (
    "🔒 Yeh feature is demo school mein band hai.\n\n"
    "Lekin fikar na karein — **150 tayyar sabaq, 150 quiz, awaaz aur "
    "tasveerein** sab kaam kar rahe hain! Lesson Bank kholein aur "
    "seekhna shuru karein."
)

# ===========================================================================
# CLOUD STORAGE — AI4Kids.pk
# ---------------------------------------------------------------------------
# Jab school cloud (Railway) par chalta hai to AI4KIDS_DATA_DIR environment
# variable ek permanent disk ki taraf ishara karta hai. Sab likhne wali cheezein
# (students.json, record_room, homework, ghalti copy, caches) wahan jaati hain,
# taake app restart hone par bhi record mehfooz rahe.
#
# PC par yeh variable set NAHI hota -> DATA_DIR = app folder -> app bilkul
# pehle jaisa chalta hai. Koi farq nahi parta.
# ===========================================================================
APP_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("AI4KIDS_DATA_DIR", APP_DIR)
try:
    os.makedirs(DATA_DIR, exist_ok=True)
except Exception:
    DATA_DIR = APP_DIR


def _data(name):
    """Likhne wali file/folder ka poora raasta (cloud disk ya app folder)."""
    return os.path.join(DATA_DIR, name)


def _app(name):
    """Sirf parhne wali file ka raasta (hamesha app folder mein)."""
    return os.path.join(APP_DIR, name)


def _seed_data_dir():
    """Naye disk par pehli baar: shuru ka data ek dafa copy kar do."""
    if os.path.abspath(DATA_DIR) == os.path.abspath(APP_DIR):
        return
    import shutil as _sh
    for _n in ("students.json", "quiz_cache.json", "lesson_cache.json",
               "checkpoint_cache.json", "fitb_cache.json", "ghalti_copy.json",
               "juma_test_cache.json", "urdu_summary_cache.json",
               "homework_diary.json", "agent_cache.json"):
        _s, _d = _app(_n), _data(_n)
        if os.path.exists(_s) and not os.path.exists(_d):
            try:
                _sh.copy2(_s, _d)
            except Exception:
                pass
    for _n in ("record_room", "tts_cache"):
        _s, _d = _app(_n), _data(_n)
        if os.path.isdir(_s) and not os.path.isdir(_d):
            try:
                _sh.copytree(_s, _d)
            except Exception:
                pass


_seed_data_dir()

RECORD_ROOM = _data("record_room")
REGISTER_FILE = _data("students.json")
QUIZ_CACHE_FILE = _data("quiz_cache.json")
SECTIONS = ["Chaand", "Sitara", "Gulab", "Shaheen"]

# ---------------------------------------------------------------------------
# SHARED SCHOOL IDENTITY
# ---------------------------------------------------------------------------
BRAND = """
You work for AI4Kids.pk — Islamabad ka pehla Urdu AI school — an online school
teaching Pakistani children in Grades 1-10.

House style:
- ROMAN URDU ONLY. Sab kuch Roman Urdu mein likho. English script mein
  Urdu bolna hai. Na English paragraphs likho, na Urdu script (اردو) use karo.
  Technical terms English mein rakh sakte ho lekin explanation Roman Urdu mein.
  Example: "AI ka matlab hai Artificial Intelligence — yani ek aisi machine
  jo khud soch sakti hai aur seekh sakti hai."
- Pakistani cultural examples ONLY: biryani, rickshaws, cricket, bazaars,
  truck art, Islamabad landmarks, Pakistani seasons and festivals.
- Grade bands: Gr 1-2 bohat simple, Gr 3-4 thora mushkil, Gr 5+ aur zyada deep.
- Gamified: stars, badges, levels (Pilot/Explorer/Commander/Astronaut).
- Kid-safe hamesha. Pyar se sikhaao. Hosla afzai karo.

SCHOOL RITUALS:
- Apna job title bataao. Garm andaaz mein baat karo (Assalam-o-Alaikum).
- Agar student ki details milein, to bachay ko naam se pukaaro.
- Mehnat ki tareef karo, stars do. Streak celebrate karo.
"""

# ---------------------------------------------------------------------------
# SUBJECT TEACHERS — each subject has its own teacher + prompt
# ---------------------------------------------------------------------------
AI_TEACHER = BRAND + """
ROLE: Ustaad Ji — AI & Technology Teacher.
Teach AI concepts: what is AI, robots, machine learning, neural networks,
chatbots, computer vision — matched to grade level.
Every lesson: Title (Eng+Urdu), "Chalo Seekhte Hain!" hook, ONE Pakistani
example, hands-on activity, 2-3 review questions, star reward.
Sign off as Ustaad Ji.
"""

ROBOTICS_TEACHER = BRAND + """
ROLE: Robotics Ustaad — Automation & Robotics Teacher.
Teach robotics and automation: sensors, motors, Arduino, drones, factory
robots, simple machines, gears, pulleys — matched to grade level.
Use Pakistani examples: automatic flour mill, textile factory, rickshaw
engine, sugarcane juice machine, traffic signals.
Every lesson: Title (Eng+Urdu), fun intro, ONE Pakistani machine example,
hands-on build activity, review questions, star reward.
Sign off as Robotics Ustaad.
"""

ENGLISH_TEACHER = BRAND + """
ROLE: English Ma'am — English Language Teacher.
Teach English: phonics, grammar, vocabulary, reading, creative writing,
comprehension, essay writing — matched to grade level.
Use Pakistani context: stories set in Islamabad, letters about Eid,
essays about cricket, comprehension about Pakistani heroes.
Lower grades: ABCs, sight words, simple sentences.
Upper grades: paragraphs, essays, story writing, grammar rules.
Every lesson: Title, warm intro, clear explanation with examples,
practice exercise, star reward. Sign off as English Ma'am.
"""

MATH_TEACHER = BRAND + """
ROLE: Hisaab Sir — Mathematics Teacher.
Teach math: counting, addition, subtraction, multiplication, division,
fractions, geometry, word problems — matched to grade level.
Use Pakistani examples: bazaar shopping (rupees), cricket scores,
sharing samosas equally, measuring truck art designs, rickshaw fares.
Every lesson: Title (Eng+Urdu), real-life hook, step-by-step method,
3 practice problems with Pakistani context, star reward.
Sign off as Hisaab Sir.
"""

SCIENCE_TEACHER = BRAND + """
ROLE: Science Sir — General Science Teacher.
Teach science: human body, plants, animals, water cycle, weather,
electricity, magnets, solar system, simple experiments — grade matched.
Use Pakistani examples: monsoon rains, Tarbela Dam, Margalla Hills
wildlife, cotton and wheat crops, Karachi coastline, Hunza valley.
Every lesson: Title (Eng+Urdu), "Kya tumne socha?" curiosity hook,
simple explanation, ONE safe home experiment, review questions, star.
Sign off as Science Sir.
"""

EXAMINER_PROMPT = BRAND + """
ROLE: Examiner Sahib. You create fun, fair assessments for ANY subject.
You will be told the subject and topic. Create grade-appropriate quiz.
Every quiz: Title + subject + grade, 5 questions (MCQs + fill-blank +
thinking question), bilingual wording, ANSWER KEY with explanations,
star scoring guide. Sign off as Examiner Sahib.
"""

MCQ_EXAMINER_PROMPT = BRAND + """
ROLE: Examiner Sahib. Create EXACTLY 5 MCQ questions in JSON format.
You will be told the subject, topic, grade level, and DIFFICULTY LEVEL.

DIFFICULTY LEVELS:
- "easy": Simple sawaal, obvious jawab, one grade BELOW level. Hints dein.
- "medium": Grade-appropriate sawaal. Normal difficulty.
- "hard": Tricky sawaal, mixed concepts, one grade ABOVE level.

ONLY valid JSON, no other text. Format:
{"title":"Quiz title","difficulty":"easy/medium/hard","questions":[{"q":"Question?","a":"Option A","b":"Option B","c":"Option C","d":"Option D","correct":"a","explanation":"Kyun sahi hai"}]}

Rules:
- EXACTLY 5 questions. correct = lowercase "a","b","c","d"
- Match the DIFFICULTY LEVEL given. ROMAN URDU ONLY. Pakistani examples.
- NO text outside JSON
"""

CLASS_TEACHER_PROMPT = BRAND + """
ROLE: Class Teacher — the friendly teacher kids chat with every day.
Short warm answers. One idea at a time. Guide, don't give answers.
If off-topic, redirect gently. Celebrate effort with stars.
"""

ADMIN_OFFICE_PROMPT = BRAND + """
ROLE: Admin Office & Cashier. Handle parents and admin professionally.
Respectful tone. Don't invent facts — use placeholders.
Close as "Admin Office, AI4Kids.pk".
"""

# ---------------------------------------------------------------------------
# SUBJECTS CONFIG — one dict rules all classrooms
# ---------------------------------------------------------------------------
SUBJECTS = {
    "ai": {
        "name": "AI & Technology (Lazmi)",
        "urdu": "ٹیکنالوجی",
        "teacher": "Ustaad Ji",
        "emoji": "🤖",
        "color": "#1abc9c",
        "bg": "#e8f8f5",
        "border": "#16a085",
        "prompt": AI_TEACHER,
        "folder": "ai_lessons",
        "wall": "Circuit boards, robot posters, laptop stickers",
        "topics": {
            1: [
                ("AI kya hai?", "Lazmi: AI kya hota hai? Simple intro — machine jo sochti hai"),
                ("Robot dost", "Lazmi: Robot kya karta hai? Hamare madadgaar robots"),
                ("Smart vs Silly machine", "Lazmi: Kaunsi machine smart hai, kaunsi silly?"),
                ("Computer pehchano", "Lazmi: Computer ke hisse — screen, keyboard, mouse"),
                ("Bolta computer", "Lazmi: Alexa, Siri — computer kaise bolta hai?"),
                ("AI games mein", "Lazmi: Video games mein AI kaise khelti hai"),
            ],
            2: [
                ("AI ki aankh", "Lazmi: Camera se computer kaise dekhta hai — face detect"),
                ("AI ke kaan", "Lazmi: Voice recognition — computer sunti hai tumhari baat"),
                ("Sorting seekho", "Lazmi: Cheezein arrange karna — AI bhi yahi karti hai"),
                ("Yes/No decisions", "Lazmi: Computer kaise faisla karti hai — haan ya nahi"),
                ("AI drawings", "Lazmi: AI se tasveerein banana — rangon ka jadoo"),
                ("AI hamare ghar mein", "Lazmi: Washing machine, AC, TV mein AI"),
            ],
            3: [
                ("Patterns dhundho", "Lazmi: AI patterns kaise dhundhti hai — numbers aur shapes mein"),
                ("Data kya hai?", "Lazmi: Data matlab information — tumhara naam bhi data hai"),
                ("Algorithm", "Lazmi: Steps ka plan — jaise biryani ki recipe ek algorithm hai"),
                ("AI aur cricket", "Lazmi: DRS, Hawk-Eye — AI cricket mein kaise madad karti hai"),
                ("Coding intro", "Lazmi: Computer ko instructions dena — pehla code"),
                ("AI safe istemal", "Lazmi: Internet safety — kya share karein kya nahi"),
            ],
            4: [
                ("Machine learning", "Lazmi: Computer khud seekhti hai — examples se training"),
                ("Chatbot kya hai", "Lazmi: ChatGPT, Claude — AI se baat karna"),
                ("Data types", "Lazmi: Text, numbers, images, audio — sab data hai"),
                ("AI decision tree", "Lazmi: Agar yeh to woh — decision tree banana"),
                ("Fake vs real", "Lazmi: AI se bani fake images pehchano — deepfakes"),
                ("AI jobs", "Lazmi: AI se kaunse kaam hote hain — future careers"),
            ],
            5: [
                ("Neural network", "Lazmi: Dimaag jaisa computer — neurons aur connections"),
                ("Prompt engineering", "Lazmi: AI se achi baat kaise karein — best prompts likhna"),
                ("Computer vision", "Lazmi: AI tasveerein kaise samajhti hai — object detection"),
                ("NLP basics", "Lazmi: AI language kaise samajhti hai — Natural Language Processing"),
                ("AI ethics", "Lazmi: AI ka sahi aur ghalat istemal — zimmedari"),
                ("AI project", "Lazmi: Apna chhota AI project design karo — idea to plan"),
            ],
            "high": [
                ("Deep learning", "Neural networks ki layers — CNN, RNN basics"),
                ("AI tools", "GitHub Copilot, MidJourney, Claude — hands on"),
                ("Python for AI", "Python basics — AI ke liye programming"),
                ("Data science", "Data clean karna, analyze karna, visualize karna"),
                ("AI in Pakistan", "Pakistan mein AI startups aur opportunities"),
                ("Capstone project", "Apna AI project banao — start to finish"),
            ],
        },
    },
    "robotics": {
        "name": "Automation & Robotics",
        "urdu": "روبوٹکس",
        "teacher": "Robotics Ustaad",
        "emoji": "⚙️",
        "color": "#f39c12",
        "bg": "#fef9e7",
        "border": "#e67e22",
        "prompt": ROBOTICS_TEACHER,
        "folder": "robotics_lessons",
        "wall": "Gear models, robot gallery, motor diagrams",
        "topics": {
            "low": [
                ("Machine kya hai?", "Simple machines — lever, wheel"),
                ("Robot kya karta?", "Robots kya kya kar sakte hain"),
                ("Sensor dost", "Sensors — robot ki aankhein aur kaan"),
                ("Motor chalo!", "Motor kaise ghoomta hai"),
                ("Traffic light", "Traffic signal kaise kaam karta hai"),
                ("Toy robot", "Apna toy robot design karo"),
            ],
            "mid": [
                ("Arduino intro", "Arduino kya hai? Chhota computer"),
                ("Drone udaan", "Drone kaise udta hai"),
                ("Factory robot", "Factory mein robot kya karta hai"),
                ("Line follower", "Line follow karne wala robot"),
                ("Automatic gate", "Automatic darwaza kaise khulta hai"),
                ("Robotic arm", "Robotic arm — haath jaisa robot"),
            ],
            "high": [
                ("IoT basics", "Internet of Things kya hai"),
                ("3D printing", "3D printer se cheezein banana"),
                ("AI + Robotics", "Jab AI robot mein aaye"),
                ("Self-driving car", "Khud chalti gaari ka system"),
                ("Space robots", "Space mein robots"),
                ("Future tech", "Pakistan mein automation ka mustaqbil"),
            ],
        },
    },
    "english": {
        "name": "English",
        "urdu": "انگریزی",
        "teacher": "English Ma'am",
        "emoji": "📚",
        "color": "#9b59b6",
        "bg": "#f5eef8",
        "border": "#8e44ad",
        "prompt": ENGLISH_TEACHER,
        "folder": "english_lessons",
        "wall": "Alphabet charts, storybook covers, word wall",
        "topics": {
            1: [
                ("Alphabets aur Phonics", "SNC: A-Z upper/lower case, letter sounds, blending"),
                ("Sight words", "SNC: High-frequency words — the, is, am, are, my, this"),
                ("Mera ghar meri family", "SNC: My family, body parts — simple sentences"),
                ("Animals aur colors", "SNC: Animals, colors, numbers — vocabulary building"),
                ("Story time", "SNC: Short stories with pictures — reading aur listening"),
                ("Writing practice", "SNC: Letters aur words trace karo, copy karo"),
            ],
            2: [
                ("Paragraphs parhna", "SNC: Short paragraphs aur stories reading"),
                ("Nouns aur verbs", "SNC: Grammar — nouns (naam) aur verbs (kaam ke alfaaz)"),
                ("School aur ghar", "SNC: Vocabulary — school, home, food, clothes, weather"),
                ("Sentences banana", "SNC: Statements aur questions likhna"),
                ("Listening skills", "SNC: 2-3 step instructions follow karna"),
                ("Picture describe karo", "SNC: Speaking — tasveeron ke baare mein batao"),
            ],
            3: [
                ("Stories aur poems", "SNC: Reading fiction, poetry — comprehension questions"),
                ("Grammar: Nouns types", "SNC: Common/proper nouns, pronouns, adjectives"),
                ("Tenses intro", "SNC: Simple present aur past tense"),
                ("Punctuation", "SNC: Full stop, question mark, comma ka istemal"),
                ("Paragraph likhna", "SNC: 5-6 sentences ka paragraph likhna"),
                ("Letter writing", "SNC: Informal letter — dost ko khat likho"),
            ],
            4: [
                ("Fiction aur non-fiction", "SNC: Stories, articles, poetry parhna — inference nikalna"),
                ("Grammar advanced", "SNC: Adverbs, prepositions, conjunctions seekho"),
                ("Tenses: Present Past Future", "SNC: Simple aur continuous tenses"),
                ("Vocabulary building", "SNC: Prefixes, suffixes, compound words"),
                ("Essay aur diary", "SNC: Short essays, diary entries likhna"),
                ("Formal letter", "SNC: Formal aur informal letter writing"),
            ],
            5: [
                ("Comprehension skills", "SNC: Summarize, predict, infer — longer texts se"),
                ("Active/Passive voice", "SNC: Active voice ko passive mein badalna"),
                ("All tenses review", "SNC: Past, present, future — simple, continuous, perfect"),
                ("Idioms aur proverbs", "SNC: Muhavare aur kahawatein — context clues"),
                ("Essay aur story writing", "SNC: Essays, stories, book reviews likhna"),
                ("Creative writing", "SNC: Poetry, dialogue, application letter likhna"),
            ],
            "high": [
                ("Advanced grammar", "Articles, modals, conditionals, reported speech"),
                ("Comprehension advanced", "Critical reading, author's purpose, bias"),
                ("Formal writing", "Reports, emails, persuasive writing"),
                ("Literature", "Short stories, poems analysis, themes"),
                ("Debate skills", "Arguments banana, public speaking"),
                ("Vocabulary mastery", "Root words, word families, academic words"),
            ],
        },
    },
    "math": {
        "name": "Hisaab (Math)",
        "urdu": "حساب",
        "teacher": "Hisaab Sir",
        "emoji": "🔢",
        "color": "#27ae60",
        "bg": "#eafaf1",
        "border": "#1e8449",
        "prompt": MATH_TEACHER,
        "folder": "math_lessons",
        "wall": "Times tables, shapes poster, number line",
        "topics": {
            1: [
                ("Ginti 0-100", "SNC: Numbers 0-100 — pehchano, likho, gino, compare karo"),
                ("Jama (+)", "SNC: Addition without carrying — 1-digit aur 2-digit numbers"),
                ("Minus (-)", "SNC: Subtraction without borrowing — kitne bach gaye?"),
                ("Pakistani Paisa", "SNC: Coins Rs1,2,5,10 aur Notes Rs10,20,50,100 pehchano"),
                ("Ghadi Parhna", "SNC: Analog clock, digital clock, din aur maheene"),
                ("Ashkaal", "SNC: Rectangle, square, circle, triangle — pehchano aur match karo"),
            ],
            2: [
                ("Numbers 999 tak", "SNC: 3-digit numbers, place value — hundreds, tens, ones"),
                ("Jama carrying ke saath", "SNC: 2-digit aur 3-digit addition with carrying"),
                ("Minus borrowing ke saath", "SNC: 2-digit aur 3-digit subtraction with borrowing"),
                ("Zarb ki tables", "SNC: Multiplication tables 2,3,4,5,10 — repeated addition se"),
                ("Taqseem", "SNC: Division symbol, divide within tables, zero remainder"),
                ("Fractions intro", "SNC: Half, one-third, quarter — barabar hisse"),
            ],
            3: [
                ("Roman numbers", "SNC: Roman numbers I se XX tak likhna aur parhna"),
                ("4-digit operations", "SNC: Addition/subtraction up to 4-digit, mental math 100 tak"),
                ("Zarb tables 6-9", "SNC: Multiplication tables 6,7,8,9 — 2-digit x 1-digit"),
                ("Fractions", "SNC: Proper, improper, equivalent — add/subtract same denominator"),
                ("Naap taul", "SNC: Kilometer, meter, cm, kg, gram, liter, mL — perimeter"),
                ("Data handling", "SNC: Carroll diagram, tally chart, picture graph parhna"),
            ],
            4: [
                ("Numbers 1 lakh tak", "SNC: 100,000 tak numbers, place value 6-digit"),
                ("Factors aur multiples", "SNC: Prime/composite, divisibility 2,3,5,10, prime factorization"),
                ("Fractions operations", "SNC: Like/unlike, improper to mixed, multiply, divide fractions"),
                ("Decimals", "SNC: Decimal place value, fraction to decimal, add/subtract/multiply"),
                ("Naap conversions", "SNC: km-m, kg-g, L-mL convert karo, 24-hour time"),
                ("Geometry angles", "SNC: Protractor se angles naapna, acute/obtuse/right, parallel lines"),
            ],
            5: [
                ("Numbers 10 lakh tak", "SNC: 1,000,000 tak — multiply/divide by 10,100,1000"),
                ("HCF aur LCM", "SNC: Prime factorization se HCF/LCM nikalna, real life problems"),
                ("Decimals aur percentage", "SNC: 3-decimal places, percentage to fraction, real life %"),
                ("Fractions advanced", "SNC: Different denominators, multiply/divide fractions"),
                ("Geometry shapes", "SNC: Triangles (equilateral/isosceles/scalene), quadrilaterals, symmetry"),
                ("Perimeter aur area", "SNC: Square/rectangle formulas, real life area problems"),
            ],
            "high": [
                ("Algebra intro", "Variables, expressions, simple equations"),
                ("Ratio aur proportion", "Ratio, proportion, unitary method advanced"),
                ("Geometry advanced", "Circle area, volume of 3D shapes"),
                ("Statistics", "Mean, median, mode, probability intro"),
                ("Number systems", "Integers, rational numbers, number line"),
                ("Problem solving", "Multi-step word problems, logical reasoning"),
            ],
        },
    },
    "science": {
        "name": "General Science",
        "urdu": "سائنس",
        "teacher": "Science Sir",
        "emoji": "🔬",
        "color": "#e74c3c",
        "bg": "#fdedec",
        "border": "#c0392b",
        "prompt": SCIENCE_TEACHER,
        "folder": "science_lessons",
        "wall": "Solar system, plant diagram, body poster",
        "topics": {
            1: [
                ("Mera jism", "SNC: Jism ke hisse aur unke kaam — haath, pair, aankh"),
                ("Paanch hasiyaat", "SNC: 5 senses — dekhna, sunna, chhoona, chakhna, soonghna"),
                ("Janwar", "SNC: Ghar ke janwar aur junglee janwar — farq seekho"),
                ("Podhe", "SNC: Podhe ke hisse — jar, tana, patti, phool"),
                ("Sehat aur safai", "SNC: Healthy khana, haath dhona, safai ki aadat"),
                ("Mausam", "SNC: Dhoop, baarish, badal, hawa — Pakistan ka mausam"),
            ],
            2: [
                ("Zinda aur be-jaan", "SNC: Living aur non-living cheezein pehchano"),
                ("Janwar ki qismein", "SNC: Zameen, paani, hawa ke janwar"),
                ("Podha kaise ugta hai", "SNC: Beej se podha — seed to plant journey"),
                ("Khana ki qismein", "SNC: Energy food, body-building food, protective food"),
                ("Paani ki ahmiyat", "SNC: Paani ke uses, paani bachao"),
                ("Pakistan ke seasons", "SNC: Garmi, sardi, barsat, bahar — Pakistan mein"),
            ],
            3: [
                ("Haddiyaan aur muscles", "SNC: Human body — bones, muscles, teeth"),
                ("Sehatmand aadat", "SNC: Exercise, neend, balanced diet"),
                ("Matter: solid liquid gas", "SNC: Cheezein teen qisam ki — thos, maaye, gas"),
                ("Paani ka safar", "SNC: Water cycle — evaporation, condensation, baarish"),
                ("Din aur raat", "SNC: Zameen ghumti hai — din kyun aata hai raat kyun"),
                ("Community helpers", "SNC: Doctor, teacher, farmer, police — hamare madadgaar"),
            ],
            4: [
                ("Hazam ka nizam", "SNC: Digestive system — khana kaise hazam hota hai"),
                ("Taqat aur harkat", "SNC: Force and motion — push, pull, friction"),
                ("Simple machines", "SNC: Lever, pulley, wheel — kaam asaan karte hain"),
                ("Roshni aur saya", "SNC: Light sources, shadows, reflection"),
                ("Awaaz", "SNC: Sound sources, loud/soft, high/low pitch"),
                ("Solar system", "SNC: Suraj, zameen, chaand, sitare — hamare solar system"),
            ],
            5: [
                ("Khoon ka nizam", "SNC: Circulatory system — dil, khoon, nassen"),
                ("Cells", "SNC: Cell — jism ki sab se chhoti eent, basic unit of life"),
                ("Bijli ke circuits", "SNC: Electricity — circuits, conductors, insulators"),
                ("Magnet ki taqat", "SNC: Magnetism — poles, attraction, repulsion"),
                ("Ecosystem", "SNC: Margalla Hills ecosystem — food web, conservation"),
                ("Technology aur safety", "SNC: Computers, internet safety, digital literacy"),
            ],
            "high": [
                ("Chemistry intro", "Atoms, molecules, elements, periodic table basics"),
                ("Physics forces", "Gravity, Newton's laws, pressure"),
                ("Biology systems", "Respiratory, nervous, reproductive systems"),
                ("Earth science", "Earthquakes, volcanoes, plate tectonics"),
                ("Energy forms", "Kinetic, potential, thermal, nuclear energy"),
                ("Environment", "Climate change, pollution, renewable energy"),
            ],
        },
    },
}

# ---------------------------------------------------------------------------
# TIMETABLE — rotates by day of week
# ---------------------------------------------------------------------------
TIMETABLES = {
    0: ["math", "english", "science", "ai", "robotics"],       # Monday
    1: ["english", "science", "math", "robotics", "ai"],       # Tuesday
    2: ["science", "ai", "english", "math", "robotics"],       # Wednesday
    3: ["math", "robotics", "ai", "english", "science"],       # Thursday
    4: ["ai", "math", "robotics", "science", "english"],       # Friday
    5: ["english", "ai", "math", "robotics", "science"],       # Saturday
    6: ["science", "math", "english", "ai", "robotics"],       # Sunday
}
PERIOD_TIMES = ["8:30", "9:15", "10:00", "11:00", "11:45"]
DAY_NAMES_UR = ["Peer", "Mangal", "Budh", "Jumeraat", "Juma", "Hafta", "Itwaar"]

# ---------------------------------------------------------------------------
# WORD OF THE DAY — rotates daily, bilingual
# ---------------------------------------------------------------------------
WORDS_OF_DAY = [
    ("Algorithm", "الگورتھم", "Steps to solve a problem — jaise biryani ki recipe!"),
    ("Data", "ڈیٹا", "Information — jaise tumhara naam, grade, aur marks"),
    ("Robot", "روبوٹ", "A machine that works by itself — kaam karne wali machine"),
    ("Sensor", "سینسر", "A device that feels things — jaise thermometer bukhar naapti hai"),
    ("Code", "کوڈ", "Instructions for computers — computer ki zabaan"),
    ("Prediction", "پیشگوئی", "Guessing what will happen — jaise mausam ka andaza"),
    ("Pattern", "پیٹرن", "A design that repeats — jaise truck art ke designs"),
    ("Artificial", "مصنوعی", "Made by humans, not nature — insaan ka banaya hua"),
    ("Intelligence", "ذہانت", "Being smart — samajhne ki taqat"),
    ("Network", "نیٹ ورک", "Things connected together — jaise doston ka group"),
    ("Pixel", "پکسل", "Tiny dot on screen — screen ki chhoti si bindi"),
    ("Binary", "بائنری", "Only 0 and 1 — computer ki ginti sirf do numbers se"),
    ("Download", "ڈاؤن لوڈ", "Getting something from internet — internet se lena"),
    ("Upload", "اپ لوڈ", "Sending to internet — internet par bhejna"),
    ("Hardware", "ہارڈ ویئر", "Parts you can touch — computer ke hisse jo chhu sakte ho"),
    ("Software", "سافٹ ویئر", "Programs inside — computer ke andar chalne wale programs"),
    ("Debug", "ڈی بگ", "Finding mistakes in code — ghaltiyan dhundhna"),
    ("Automation", "آٹومیشن", "Making machines work alone — machine khud kaam kare"),
    ("Database", "ڈیٹا بیس", "A big organized store of info — information ka godown"),
    ("Encrypt", "اینکرپٹ", "Making a secret message — khufia paigham banana"),
    ("Processor", "پروسیسر", "Computer's brain — computer ka dimaag"),
    ("Memory", "میموری", "Where computer stores things — computer ki yaaddaasht"),
    ("Drone", "ڈرون", "A flying robot — udne wala robot"),
    ("Simulation", "سمولیشن", "A pretend version — nakli tajarba"),
    ("Voltage", "وولٹیج", "Electrical pressure — bijli ka dabaao"),
    ("Gravity", "کشش ثقل", "What pulls us down — zameen ki kheenchne wali taqat"),
    ("Molecule", "مالیکیول", "Tiny tiny piece of matter — cheez ka sab se chhota hissa"),
    ("Ecosystem", "ماحولیاتی نظام", "Living things together — jandar milkar rehte hain"),
    ("Fraction", "کسر", "Part of a whole — poore ka ek hissa, jaise aadha roti"),
    ("Paragraph", "پیراگراف", "A group of sentences — jumlon ka group"),
    # ---- rebalance: more Math, English aur Science (pehle sirf computing tha) ----
    ("Multiply", "ضرب", "Same number baar baar jama — zarb, jaise 3 x 4"),
    ("Angle", "زاویہ", "Do lakeeron ka kona — jaise ghadi ki sooiyan"),
    ("Percentage", "فیصد", "Sau mein se kitna — jaise 50% matlab aadha"),
    ("Perimeter", "احاطہ", "Shakal ke charon taraf ki lambai"),
    ("Average", "اوسط", "Sab ko mila kar barabar baant do"),
    ("Noun", "اسم", "Naam wala lafz — cheez, jagah ya insaan"),
    ("Verb", "فعل", "Kaam batane wala lafz — jaise daurna, khana"),
    ("Adjective", "صفت", "Cheez ki khoobi batata hai — jaise bara, laal"),
    ("Sentence", "جملہ", "Mukammal baat — alfaaz mil kar jumla bante hain"),
    ("Punctuation", "رموز اوقاف", "Jumle ke nishaan — jaise . aur ?"),
    ("Energy", "توانائی", "Kaam karne ki taqat — jaise khane se milti hai"),
    ("Magnet", "مقناطیس", "Loha kheenchne wali cheez"),
    ("Circuit", "برقی راستہ", "Bijli ka raasta — bulb tak current jaata hai"),
    ("Digestion", "ہاضمہ", "Khana hazam hone ka amal — pet ka kaam"),
    ("Habitat", "مسکن", "Janwar ka ghar — jahan woh rehta hai"),
]

# ---- SIMPLE words for Grade 1-2: roz-marra cheezein, Roman Urdu only + emoji ----
# (word, emoji, bohat aasaan matlab)  — koi Urdu script nahi, chhote bachon ke liye
WORDS_OF_DAY_SIMPLE = [
    ("Sooraj",   "☀️", "Din mein chamakta hai, garmi deta hai"),
    ("Chaand",   "🌙", "Raat mein aasman par chamakta hai"),
    ("Paani",    "💧", "Hum peete hain, zindagi ke liye zaroori"),
    ("Darakht",  "🌳", "Bara podha — saaya aur phal deta hai"),
    ("Phool",    "🌸", "Khushboo wala, rangeen aur khoobsurat"),
    ("Barish",   "🌧️", "Baadal se paani girta hai"),
    ("Chidiya",  "🐦", "Chhoti si udne wali janwar"),
    ("Billi",    "🐱", "Ghar ka janwar — miaon miaon karti hai"),
    ("Machhli",  "🐟", "Paani mein rehti aur tairti hai"),
    ("Titli",    "🦋", "Rangeen par wali, phoolon par baithti hai"),
    ("Ginti",    "🔢", "1, 2, 3 — cheezein ginna"),
    ("Jama",     "➕", "Milana — 2 aur 2 mila kar 4"),
    ("Gol",      "⭕", "Circle ki shakal — jaise roti"),
    ("Bara",     "📏", "Size mein zyada — chhote ka ulta"),
    ("Aadha",    "🍕", "Do barabar hisson mein se ek"),
    ("Aankh",    "👁️", "Isse hum dekhte hain"),
    ("Haath",    "✋", "Isse hum pakarte aur likhte hain"),
    ("Daant",    "🦷", "Isse hum khana chabate hain"),
    ("Safai",    "🧼", "Saaf rehna — haath dhona zaroori hai"),
    ("Kitaab",   "📖", "Isme sabaq aur kahaniyan hoti hain"),
    ("Pencil",   "✏️", "Isse hum likhte aur banate hain"),
    ("Bag",      "🎒", "Isme kitaabein le kar school jaate hain"),
    ("Ghar",     "🏠", "Jahan hum apni family ke saath rehte hain"),
    ("School",   "🏫", "Jahan hum parhne aur seekhne aate hain"),
    ("Dost",     "👫", "Jis ke saath hum khelte aur hanste hain"),
    ("Computer", "💻", "Machine jo kaam karti aur seekhati hai"),
    ("Robot",    "🤖", "Machine jo khud kaam karti hai"),
    ("Mobile",   "📱", "Isse hum baat karte hain"),
    ("Screen",   "🖥️", "Jis par hum tasveer dekhte hain"),
    ("Button",   "🔘", "Isko dabate hain to cheez chalti hai"),
]

def get_word_of_day():
    day_num = datetime.date.today().toordinal() % len(WORDS_OF_DAY)
    return WORDS_OF_DAY[day_num]

def get_word_of_day_simple():
    """Aaj ka aasaan lafz — Grade 1-2 ke liye (roz badalta hai)."""
    day_num = datetime.date.today().toordinal() % len(WORDS_OF_DAY_SIMPLE)
    return WORDS_OF_DAY_SIMPLE[day_num]

def get_today_timetable():
    day = datetime.date.today().weekday()
    return TIMETABLES[day], DAY_NAMES_UR[day]

def get_topics(subject_key, grade):
    t = SUBJECTS[subject_key]["topics"]
    if grade in t:
        return t[grade]
    if grade <= 3: return t.get("low", t.get(3, []))
    elif grade <= 6: return t.get("mid", t.get(5, []))
    return t.get("high", t.get(5, []))

# ---------------------------------------------------------------------------
# AGENT ROUTING (for Admin mode)
# ---------------------------------------------------------------------------
PRINCIPAL_PROMPT = BRAND + """
ROLE: Principal. Route to the right VP. NEVER answer yourself.
- "academic" -> lessons, quizzes, teaching
- "operations" -> student help, parents, admin
Reply ONLY: {"supervisor":"academic" or "operations","reason":"..."}
"""
VP_ACADEMICS_PROMPT = BRAND + """
ROLE: VP Academics. Pick staff, give instructions. NEVER create content.
- "lesson_creator" -> lessons  - "quiz_maker" -> quizzes
Reply ONLY: {"sub_agent":"...","instructions":"..."}
"""
VP_ADMIN_PROMPT = BRAND + """
ROLE: VP Admin. Pick staff.
- "tutor_helper" -> student questions  - "parent_liaison" -> parent/admin
Reply ONLY: {"sub_agent":"...","instructions":"..."}
"""

SUB_AGENT_PROMPTS = {
    "lesson_creator": AI_TEACHER,
    "quiz_maker": EXAMINER_PROMPT,
    "tutor_helper": CLASS_TEACHER_PROMPT,
    "parent_liaison": ADMIN_OFFICE_PROMPT,
}
SUPERVISOR_PROMPTS = {"academic": VP_ACADEMICS_PROMPT, "operations": VP_ADMIN_PROMPT}
TEAM = {"academic": ["lesson_creator","quiz_maker"], "operations": ["tutor_helper","parent_liaison"]}
STAFF = {
    "lesson_creator": {"title": "🎓 Ustaad Ji", "folder": "lessons"},
    "quiz_maker":     {"title": "📝 Examiner Sahib", "folder": "quizzes"},
    "tutor_helper":   {"title": "🧑‍🏫 Class Teacher", "folder": "class_teacher"},
    "parent_liaison": {"title": "🏢 Admin Office", "folder": "admin_office"},
}

# ---------------------------------------------------------------------------
# REGISTER + HELPERS
# ---------------------------------------------------------------------------
def load_register():
    if os.path.exists(REGISTER_FILE):
        with open(REGISTER_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"students": []}

def save_register(reg):
    with open(REGISTER_FILE, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)

def admit_student(reg, name, grade):
    existing_rolls = [s["roll"] for s in reg["students"]]
    roll = max(existing_rolls, default=0) + 1
    s = {"name": name.strip().title(), "roll": roll, "grade": grade,
         "section": SECTIONS[(roll-1) % len(SECTIONS)],
         "stars": 0, "attendance": [], "joined": datetime.date.today().isoformat()}
    reg["students"].append(s)
    save_register(reg)
    return s

def today():
    return datetime.date.today().isoformat()

def mark_attendance(reg, student):
    if today() not in student["attendance"]:
        student["attendance"].append(today())
        student["stars"] += 1
        save_register(reg)
        return True
    return False

def get_streak(student):
    """Count consecutive days of attendance ending today or yesterday."""
    att = sorted(student.get("attendance", []), reverse=True)
    if not att:
        return 0
    streak = 0
    check = datetime.date.today()
    for d in att:
        if d == check.isoformat():
            streak += 1
            check -= datetime.timedelta(days=1)
        elif d == (check).isoformat():
            continue
        else:
            break
    return streak

def streak_badge(streak):
    """Return emoji badge based on streak length."""
    if streak >= 30: return "🏆👑", "LEGEND! 30 din!"
    if streak >= 15: return "💎🔥", "Diamond streak! 15 din!"
    if streak >= 10: return "🌟🔥", "Super streak! 10 din!"
    if streak >= 7:  return "🔥🔥", "Hafta mukammal! 7 din!"
    if streak >= 5:  return "🔥",   "5 din ka streak!"
    if streak >= 3:  return "✨",   "3 din lagataar!"
    if streak >= 1:  return "⚡",   "Aaj hazir!"
    return "", "Kal se aao!"

def student_context(student):
    if not student: return ""
    return (f"\n\n[STUDENT: {student['name']}, Roll {student['roll']}, "
            f"Grade {student['grade']}, {student['section']}, Stars: {student['stars']}]")

def get_student_by_roll(roll):
    for s in load_register()["students"]:
        if s["roll"] == roll: return s
    return None

def get_mode(grade):
    """UI tier gated on student grade.
    Grade 1-2 -> SIMPLE, Grade 3-4 -> STANDARD, Grade 5 -> FULL.
    Note: stored in st.session_state.ui_mode (NOT .mode, which is the
    app-level door/admin/student router)."""
    try:
        g = int(grade)
    except (TypeError, ValueError):
        g = 3
    if g <= 2:
        return "SIMPLE"
    if g <= 4:
        return "STANDARD"
    return "FULL"

# ---------------------------------------------------------------------------
# CORE AGENT CALLS
# ---------------------------------------------------------------------------
def run_agent(system_prompt, task, max_tokens=2000):
    if not AI_ENABLED:
        return AI_OFF_MESSAGE
    r = client.chat.completions.create(model=MODEL, max_tokens=max_tokens,
        messages=[{"role":"system","content":system_prompt},
                  {"role":"user","content":task}])
    return r.choices[0].message.content.strip()

# ---------------------------------------------------------------------------
# URDU SUMMARY — convert a Roman-Urdu lesson into short, proper Urdu SCRIPT
# so the "Sunlo" voice reads it with correct Pakistani pronunciation.
# Cached to disk so each summary is generated only once (zero repeat API cost).
# ---------------------------------------------------------------------------
URDU_SUMMARY_PROMPT = (
    "Aap ek Pakistani ustaad hain. Aapko ek sabaq diya jaayega. "
    "Us ka aasaan khulasa SIRF Roman Urdu mein likhein — yaani English haroof mein Urdu bolna hai. "
    "Misaal: 'AI ka matlab hai Artificial Intelligence — ek aisi machine jo khud soch sakti hai.' "
    "3 se 5 chhote Roman Urdu jumlon mein likho. "
    "Urdu script (اردو) bilkul nahi likhni — sirf Roman Urdu. "
    "Koi English paragraph nahi — sirf Roman Urdu mein samjhao."
)
URDU_SUMMARY_CACHE = _data("urdu_summary_cache.json")

def get_urdu_summary(subject, topic, grade, content):
    key = cache_key(subject, topic, grade)
    cache = {}
    if os.path.exists(URDU_SUMMARY_CACHE):
        with open(URDU_SUMMARY_CACHE, encoding="utf-8") as f:
            cache = json.load(f)
    if key in cache:
        return cache[key]
    summary = run_agent(URDU_SUMMARY_PROMPT, f"Sabaq: {topic}\n\n{content}", 800)
    cache[key] = summary
    with open(URDU_SUMMARY_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    return summary

def parse_json(text):
    c = text.replace("```json","").replace("```","").strip()
    return json.loads(c[c.find("{"):c.rfind("}")+1])

def format_options(text):
    """Put quiz options a) b) c) d) on separate lines with bold letters."""
    import re
    # Add line break + bold before option markers like "a)" "b)" "c)" "d)"
    text = re.sub(r'\s+([a-dA-D])\)\s*', r'\n\n**\1)** ', text)
    return text

# ---------------------------------------------------------------------------
# ADMIN CHAT COST CONTROL — cache answers + skip routing calls when obvious
# ---------------------------------------------------------------------------
AGENT_CACHE_FILE = _data("agent_cache.json")

def load_agent_cache():
    if os.path.exists(AGENT_CACHE_FILE):
        try:
            with open(AGENT_CACHE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_agent_cache(cache):
    with open(AGENT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def agent_cache_key(user_request, student):
    g = student.get("grade") if student else "-"
    return f"g{g}|{' '.join(user_request.split()).strip().lower()}"

def quick_route(user_request):
    """Decide the staff member WITHOUT calling the API.
    Returns a sub_agent key, or None if we should ask the Principal/VP."""
    r = user_request.lower()
    if "quiz" in r or "imtehaan" in r or "test" in r:
        return "quiz_maker"
    if "lesson" in r or "sabaq" in r or "parhao" in r:
        return "lesson_creator"
    if "parent" in r or "admission" in r or "daakhla" in r or "fee" in r:
        return "parent_liaison"
    return None

def handle_request(user_request, student=None, force=False):
    """Returns (sub_agent_key, answer, from_cache).

    Cost path:
      cached        -> 0 API calls
      quick_route   -> 1 API call  (skips Principal + VP routing)
      fallback      -> 3 API calls (original Principal -> VP -> staff chain)
    """
    ctx = student_context(student)
    cache = load_agent_cache()
    ck = agent_cache_key(user_request, student)

    if not force and ck in cache:
        e = cache[ck]
        return e.get("staff", "tutor_helper"), e.get("answer", ""), True

    sa = quick_route(user_request)
    if sa:
        # 1 API call — routing is obvious, no need to pay the Principal + VP
        task = f"Request: {user_request}{ctx}"
        ans = run_agent(SUB_AGENT_PROMPTS[sa], task, 3000)
    else:
        # Original 3-agent chain for ambiguous requests
        d = parse_json(run_agent(PRINCIPAL_PROMPT, user_request, 300))
        sup = d.get("supervisor","operations")
        if sup not in SUPERVISOR_PROMPTS: sup = "operations"
        p = parse_json(run_agent(SUPERVISOR_PROMPTS[sup], user_request+ctx, 500))
        sa = p.get("sub_agent","")
        if sa not in TEAM[sup]: sa = TEAM[sup][0]
        task = f"Request: {user_request}{ctx}\n\nVP brief: {p.get('instructions',user_request)}"
        ans = run_agent(SUB_AGENT_PROMPTS[sa], task, 3000)

    cache[ck] = {"staff": sa, "answer": ans}
    save_agent_cache(cache)
    return sa, ans, False

def save_record(folder, request, answer, student=None):
    path_dir = os.path.join(RECORD_ROOM, folder)
    os.makedirs(path_dir, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    who = f"_{student['name']}_r{student['roll']}" if student else ""
    path = os.path.join(path_dir, f"{stamp}{who}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Request\n{request}\n\n")
        if student:
            f.write(f"# Student: {student['name']} (Roll {student['roll']}, Gr {student['grade']})\n\n")
        f.write(f"# Answer\n{answer}\n")
    return path

def record_label(fp, fn):
    """Human-readable, topic-related label for a Record Room entry.
    Prefers the saved request/topic from the file; falls back to a cleaned
    filename. Returns (title, date_str)."""
    import re as _re
    base = _re.sub(r'\.(md|txt)$', '', fn, flags=_re.I)
    # pull a date for the caption (either 2026-07-22_21-33-04 or 20260715_100350)
    dm = _re.search(r'(\d{4}-\d{2}-\d{2})[_-](\d{2}-\d{2}-\d{2})', base) \
         or _re.search(r'(\d{4})(\d{2})(\d{2})[_-]?(\d{2})(\d{2})?', base)
    date_str = dm.group(0).replace('_', ' ') if dm else ""
    title = ""
    try:
        with open(fp, encoding="utf-8") as f:
            txt = f.read(2000)
        m = _re.search(r'#\s*Request\s*\n(.+)', txt)
        if m:
            req = m.group(1).strip()
            mq = _re.search(r"quiz about ['\"]([^'\"]+)['\"]", req, _re.I)
            ml = _re.search(r'lesson[:\-]\s*(.+)', req, _re.I)
            if mq:
                title = "📝 Quiz: " + mq.group(1)
            elif ml:
                title = "📖 " + ml.group(1)
            else:
                title = req
    except Exception:
        pass
    if not title:                       # fallback: clean up the filename
        t = _re.sub(r'^\d{4}-\d{2}-\d{2}[_-]\d{2}-\d{2}-\d{2}', '', base)
        t = _re.sub(r'^\d{6,8}[_-]?\d{0,6}', '', t)
        t = t.strip('_ -').replace('_', ' ')
        title = t or base
    # append student name if present in filename and not already in title
    sm = _re.search(r'_([A-Za-z]+ [A-Za-z]+)_r\d+', base)
    if sm and sm.group(1) not in title:
        title += f"  ·  {sm.group(1)}"
    title = title.strip().rstrip('.')
    if len(title) > 75:
        title = title[:75] + "…"
    return (title or base), date_str

# ---------------------------------------------------------------------------
# QUIZ CACHE — save generated quizzes, reuse to save API cost
# ---------------------------------------------------------------------------
def load_quiz_cache():
    if os.path.exists(QUIZ_CACHE_FILE):
        with open(QUIZ_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_quiz_cache(cache):
    with open(QUIZ_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def cache_key(subject, topic, grade):
    """Create a unique key like 'ai_AIkyahai_gr5'."""
    band = "low" if grade <= 3 else "mid" if grade <= 6 else "high"
    clean_topic = topic.replace(" ", "").replace("?", "").replace("!", "")[:20]
    return f"{subject}_{clean_topic}_{band}"

def get_cached_quiz(subject, topic, grade):
    cache = load_quiz_cache()
    key = cache_key(subject, topic, grade)
    if key in cache and len(cache[key]) > 0:
        # Return a random quiz from cache (multiple quizzes per topic possible)
        import random
        return random.choice(cache[key])
    return None

def save_quiz_to_cache(subject, topic, grade, quiz_data):
    cache = load_quiz_cache()
    key = cache_key(subject, topic, grade)
    if key not in cache:
        cache[key] = []
    # Keep max 3 quizzes per topic (variety for repeat attempts)
    if len(cache[key]) < 3:
        cache[key].append(quiz_data)
    save_quiz_cache(cache)

# ---------------------------------------------------------------------------
# LESSON CACHE — generate each lesson once, reuse forever (zero API cost)
# ---------------------------------------------------------------------------
LESSON_CACHE_FILE = _data("lesson_cache.json")

def get_cached_lesson(subject, topic, grade):
    if os.path.exists(LESSON_CACHE_FILE):
        with open(LESSON_CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
        return cache.get(cache_key(subject, topic, grade))
    return None

def save_lesson_to_cache(subject, topic, grade, content):
    cache = {}
    if os.path.exists(LESSON_CACHE_FILE):
        with open(LESSON_CACHE_FILE, encoding="utf-8") as f:
            cache = json.load(f)
    cache[cache_key(subject, topic, grade)] = content
    with open(LESSON_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

# ---------------------------------------------------------------------------
# KNOWLEDGE BASE — pre-built lessons, zero API cost
# ---------------------------------------------------------------------------
KB_DIR = _app("kb")

def load_kb_topic(subject_key, grade, topic_title):
    """Load a pre-built lesson+quiz from knowledge base."""
    filepath = os.path.join(KB_DIR, f"grade_{grade}", f"{subject_key}.json")
    if not os.path.exists(filepath):
        return None, None
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    for topic in data.get("topics", []):
        if topic["title"] == topic_title:
            return topic.get("lesson"), topic.get("quiz")
    return None, None

def load_kb_topic_full(subject_key, grade, topic_title):
    """Return the FULL topic dict (incl. SIMPLE fields emoji/text_simple/
    audio_text/simple_quiz when present). Used only by SIMPLE mode so the
    STANDARD/FULL load_kb_topic path is untouched."""
    filepath = os.path.join(KB_DIR, f"grade_{grade}", f"{subject_key}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    for topic in data.get("topics", []):
        if topic["title"] == topic_title:
            return topic
    return None


def render_topic_interactive(subject_key, grade, topic_title):
    """Embed a Class 5 HTML micro-lesson (interactives/) above the text sabaq."""
    import streamlit.components.v1 as components
    topic = load_kb_topic_full(subject_key, grade, topic_title) or {}
    rel = topic.get("interactive_file")
    if not rel:
        FALLBACK = {
            (5, "math", "Numbers 10 lakh tak"): "interactives/g5-place-value.html",
            (5, "math", "HCF aur LCM"): "interactives/g5-hcf-lcm.html",
            (5, "math", "Fractions advanced"): "interactives/g5-fractions-advanced.html",
            (5, "math", "Perimeter aur area"): "interactives/g5-perimeter-area.html",
    (5, "math", "Decimals aur percentage"): "interactives/g5-decimals-percentage.html",
            (5, "science", "Cells"): "interactives/g5-cells.html",
            (5, "science", "Khoon ka nizam"): "interactives/g5-khoon-nizam.html",
            (5, "science", "Energy — forms"): "interactives/g5-energy.html",
            (5, "ai", "AI ethics"): "interactives/g5-ai-literacy.html",
            (5, "science", "Bijli ke circuits"): "interactives/g5-bijli-circuits.html",
            (5, "science", "Magnet ki taqat"): "interactives/g5-magnetism.html",
            (5, "science", "Ecosystem"): "interactives/g5-ecosystem.html",
            (5, "science", "Technology aur safety"): "interactives/g5-technology-safety.html",
            (4, "science", "Solar system"): "interactives/g4-solar-system.html",
            (3, "science", "Paani ka safar"): "interactives/g3-paani-ka-safar.html",
            (3, "science", "Matter: solid liquid gas"): "interactives/g3-states-of-matter.html",
            (4, "science", "Hazam ka nizam"): "interactives/g4-hazam-ka-nizam.html",
            (4, "science", "Taqat aur harkat"): "interactives/g4-taqat-aur-harkat.html",
    (4, "ai", "Machine learning"): "interactives/g4-machine-learning.html",
    (4, "ai", "Chatbot kya hai"): "interactives/g4-chatbot-kya-hai.html",
    (4, "ai", "Data types"): "interactives/g4-data-types.html",
    (4, "ai", "AI decision tree"): "interactives/g4-ai-decision-tree.html",
    (4, "ai", "Fake vs real"): "interactives/g4-fake-vs-real.html",
    (4, "ai", "AI jobs"): "interactives/g4-ai-jobs.html",
    (4, "english", "Fiction aur non-fiction"): "interactives/g4-fiction-nonfiction.html",
    (4, "islamiat", "Iman aur Ibadat"): "interactives/g4-iman-ibadat.html",
    (4, "islamiat", "Akhlaq aur Muamalat"): "interactives/g4-akhlaq-muamalat.html",
    (4, "islamiat", "Seerat aur Hidayat"): "interactives/g4-seerat-hidayat.html",
            (5, "ai", "Neural network"): "interactives/g5-neural-network.html",
            (5, "ai", "Prompt engineering"): "interactives/g5-prompt-engineering.html",
            (5, "ai", "AI project"): "interactives/g5-ai-project.html",
            (5, "ai", "Computer vision"): "interactives/g5-computer-vision.html",
            (5, "ai", "Binary lab — jama/tafreeq"): "interactives/g5-binary-lab.html",
    (5, "ai", "NLP basics"): "interactives/g5-nlp-basics.html",
            (5, "english", "Comprehension skills"): "interactives/g5-comprehension-skills.html",
            (5, "english", "Active/Passive voice"): "interactives/g5-active-passive-voice.html",
            (5, "english", "All tenses review"): "interactives/g5-all-tenses-review.html",
            (5, "english", "Creative writing"): "interactives/g5-creative-writing.html",
    (5, "english", "Idioms aur proverbs"): "interactives/g5-idioms-proverbs.html",
            (5, "robotics", "3D printing"): "interactives/g5-3d-printing.html",
    (5, "robotics", "AI + Robotics"): "interactives/g5-ai-robotics.html",
    (5, "robotics", "Self-driving car"): "interactives/g5-self-driving-car.html",
    (5, "robotics", "Space robots"): "interactives/g5-space-robots.html",
    (5, "robotics", "IoT basics"): "interactives/g5-iot-basics.html",
    (5, "robotics", "Future tech"): "interactives/g5-future-tech.html",
    (5, "social", "Citizenship"): "interactives/g5-citizenship.html",
    (5, "social", "Culture"): "interactives/g5-culture.html",
    (5, "social", "State aur Government"): "interactives/g5-state-government.html",
    (5, "social", "History"): "interactives/g5-history.html",
    (5, "social", "Geography"): "interactives/g5-geography.html",
    (5, "social", "Economics"): "interactives/g5-economics.html",
    (5, "islamiat", "Imaniyat aur ibadat"): "interactives/g5-imaniyat-ibadat.html",
    (5, "islamiat", "Seerat-e-Tayyiba"): "interactives/g5-seerat-tayyiba.html",
    (5, "islamiat", "Akhlaq aur aadaab"): "interactives/g5-akhlaq-aadaab.html",
    (5, "islamiat", "Husn-e-muamalat"): "interactives/g5-husn-muamalat.html",
    (5, "islamiat", "Hidayat ke sarchashme"): "interactives/g5-hidayat-sarchashme.html",
    (5, "islamiat", "Islami taleemat aaj"): "interactives/g5-islami-taleemat-aaj.html",
    (5, "urdu", "Hamd aur Naat"): "interactives/g5-hamd-naat.html",
    (5, "urdu", "Rahmat-e-Aalam aur seerat stories"): "interactives/g5-rahmat-aalam.html",
    (5, "urdu", "Qomi tehwar aur watan"): "interactives/g5-qomi-tehwar.html",
    (5, "urdu", "Kahani aur afsana"): "interactives/g5-kahani-afsana.html",
    (5, "urdu", "Grammar aur imla"): "interactives/g5-grammar-imla.html",
    (5, "urdu", "Tahrir"): "interactives/g5-tahrir.html",
        }
        rel = FALLBACK.get((int(grade), subject_key, topic_title))
    if not rel:
        return False
    fpath = _app(rel)
    if not os.path.exists(fpath):
        st.warning(f"Interactive file missing: {rel}")
        return False
    label = topic.get("interactive_label") or "Khelo — interactive"
    st.markdown(
        f'<div style="padding:10px 14px;background:#f5eef8;border-left:4px solid #8e44ad;'
        f'border-radius:0 10px 10px 0;margin:8px 0"><b>{label}</b><br>'
        f'<span style="font-size:0.85em">Neeche khelo — phir quiz lo.</span></div>',
        unsafe_allow_html=True,
    )
    try:
        html = open(fpath, encoding="utf-8").read()
        components.html(html, height=720, scrolling=True)
        return True
    except Exception as e:
        st.error(f"Interactive nahi khul saki: {e}")
        return False

def simple_text_fallback(lesson_str, max_words=70):
    """When a KB topic has no text_simple yet (pre-enrichment), build a short,
    plain Roman-Urdu blurb from the lesson markdown so SIMPLE mode still works."""
    if not isinstance(lesson_str, str):
        return "Aao is topic ko seekhein!"
    import re as _re
    txt = _re.sub(r'[#*_`>|~\-]', ' ', lesson_str)          # strip markdown
    txt = _re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', txt)     # strip links
    txt = _re.sub(r'\s+', ' ', txt).strip()
    words = txt.split()
    return " ".join(words[:max_words]) + ("..." if len(words) > max_words else "")

# ---------------------------------------------------------------------------
# ADAPTIVE QUIZ — difficulty adjusts per student per topic
# ---------------------------------------------------------------------------
DIFFICULTY_LEVELS = ["easy", "medium", "hard"]
DIFFICULTY_EMOJI = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}

def get_skill_key(subject, topic):
    clean = topic.replace(" ", "_").replace("?", "").replace("!", "")[:20]
    return f"{subject}_{clean}"

def get_student_difficulty(student, subject, topic):
    skills = student.get("skill_levels", {})
    key = get_skill_key(subject, topic)
    return skills.get(key, "medium")

def update_student_difficulty(roll, subject, topic, score, total=5):
    reg = load_register()
    for s in reg["students"]:
        if s["roll"] == roll:
            if "skill_levels" not in s:
                s["skill_levels"] = {}
            key = get_skill_key(subject, topic)
            current = s["skill_levels"].get(key, "medium")
            ci = DIFFICULTY_LEVELS.index(current)
            if score >= 4:
                new_level = DIFFICULTY_LEVELS[min(ci + 1, 2)]
            elif score <= 2:
                new_level = DIFFICULTY_LEVELS[max(ci - 1, 0)]
            else:
                new_level = current
            s["skill_levels"][key] = new_level
            save_register(reg)
            return current, new_level
    return "medium", "medium"

# ---------------------------------------------------------------------------
# GHALTI COPY — save wrong answers, replay for spaced repetition
# ---------------------------------------------------------------------------
GHALTI_FILE = _data("ghalti_copy.json")

def load_ghalti():
    if os.path.exists(GHALTI_FILE):
        with open(GHALTI_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_ghalti(data):
    with open(GHALTI_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_to_ghalti(roll, subject, topic, wrong_questions):
    """Save wrong questions to student's ghalti copy."""
    if not wrong_questions:
        return
    gc = load_ghalti()
    key = str(roll)
    if key not in gc:
        gc[key] = []
    for q in wrong_questions:
        entry = {
            "subject": subject,
            "topic": topic,
            "question": q,
            "added": today(),
            "review_count": 0,
            "last_reviewed": None,
        }
        # Avoid duplicate questions
        already = any(
            e["question"]["q"] == q["q"] and e["topic"] == topic
            for e in gc[key]
        )
        if not already:
            gc[key].append(entry)
    save_ghalti(gc)

def get_ghalti_due(roll, max_items=5):
    """Get questions due for review (added 2+ days ago or never reviewed)."""
    gc = load_ghalti()
    entries = gc.get(str(roll), [])
    today_date = datetime.date.today()
    due = []
    for e in entries:
        added = datetime.date.fromisoformat(e["added"])
        last = datetime.date.fromisoformat(e["last_reviewed"]) if e["last_reviewed"] else None
        days_since_added = (today_date - added).days
        days_since_review = (today_date - last).days if last else 999
        # Due if: never reviewed + 1+ day old, OR reviewed + 3+ days ago
        if (last is None and days_since_added >= 1) or (last and days_since_review >= 3):
            due.append(e)
    return due[:max_items]

def mark_ghalti_reviewed(roll, question_text, correct):
    """Update review record. If correct, remove permanently from ghalti copy."""
    gc = load_ghalti()
    key = str(roll)
    for e in gc.get(key, []):
        if e["question"]["q"] == question_text:
            e["last_reviewed"] = today()
            e["review_count"] += 1
            if correct:
                e["mastered"] = True
    gc[key] = [e for e in gc.get(key, []) if not e.get("mastered")]
    save_ghalti(gc)

def clear_ghalti_topic(roll, subject, topic):
    """Remove ALL ghalti entries for a topic — called when student retakes quiz and scores 4-5/5."""
    gc = load_ghalti()
    key = str(roll)
    before = len(gc.get(key, []))
    gc[key] = [e for e in gc.get(key, [])
               if not (e["subject"] == subject and e["topic"] == topic)]
    after = len(gc.get(key, []))
    if before != after:
        save_ghalti(gc)
        return before - after  # how many removed
    return 0

def clear_ghalti_correct_answers(roll, subject, topic, correct_question_texts):
    """Remove specific questions from ghalti copy that student got right in regular quiz."""
    gc = load_ghalti()
    key = str(roll)
    before = len(gc.get(key, []))
    gc[key] = [
        e for e in gc.get(key, [])
        if not (e["subject"] == subject
                and e["topic"] == topic
                and e["question"]["q"] in correct_question_texts)
    ]
    after = len(gc.get(key, []))
    if before != after:
        save_ghalti(gc)
        return before - after
    return 0

def get_ghalti_count(roll):
    """Total pending ghalti questions for a student."""
    gc = load_ghalti()
    return len(gc.get(str(roll), []))

# ---------------------------------------------------------------------------
# JUMA TEST — weekly Friday test pulling from all subjects
# ---------------------------------------------------------------------------
JUMA_TEST_FILE = _data("juma_test_cache.json")

def is_juma_today():
    return datetime.date.today().weekday() == 4  # Friday = 4

def get_this_week_monday():
    today_d = datetime.date.today()
    return today_d - datetime.timedelta(days=today_d.weekday())

def load_juma_cache():
    if os.path.exists(JUMA_TEST_FILE):
        with open(JUMA_TEST_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_juma_cache(data):
    with open(JUMA_TEST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def has_done_juma_test(roll):
    """Check if student already did this week's Juma Test."""
    jc = load_juma_cache()
    week_key = get_this_week_monday().isoformat()
    return jc.get(str(roll), {}).get(week_key, False)

def mark_juma_done(roll, score, total):
    jc = load_juma_cache()
    week_key = get_this_week_monday().isoformat()
    if str(roll) not in jc:
        jc[str(roll)] = {}
    jc[str(roll)][week_key] = {"done": True, "score": score, "total": total, "date": today()}
    save_juma_cache(jc)

def build_juma_questions(student, grade):
    """Pull 2 questions from each of 5 subjects = 10 questions total.
    Uses KB quizzes first (free), falls back to cache, skips if none available."""
    import random
    all_questions = []
    subj_keys = ["ai", "math", "english", "science", "robotics"]
    for sk in subj_keys:
        topics = get_topics(sk, grade)
        # Shuffle and try topics until we get 2 questions
        random.shuffle(list(topics))
        qs_from_subj = []
        for title, _ in topics:
            if len(qs_from_subj) >= 2:
                break
            # Try KB first
            _, kb_quiz = load_kb_topic(sk, grade, title)
            if kb_quiz and "questions" in kb_quiz and kb_quiz["questions"]:
                pool = kb_quiz["questions"]
                pick = random.sample(pool, min(2 - len(qs_from_subj), len(pool)))
                for q in pick:
                    q = dict(q)
                    q["_subject"] = SUBJECTS[sk]["name"]
                    q["_topic"] = title
                    q["_subj_key"] = sk
                    qs_from_subj.append(q)
            else:
                cached = get_cached_quiz(sk, title, grade)
                if cached and "questions" in cached:
                    pool = cached["questions"]
                    pick = random.sample(pool, min(2 - len(qs_from_subj), len(pool)))
                    for q in pick:
                        q = dict(q)
                        q["_subject"] = SUBJECTS[sk]["name"]
                        q["_topic"] = title
                        q["_subj_key"] = sk
                        qs_from_subj.append(q)
        all_questions.extend(qs_from_subj)
    random.shuffle(all_questions)
    return all_questions[:10]


# ===========================================================================
# LESSON CHECKPOINT RENDERER
# ===========================================================================
SECTION_META = {
    "HOOK":    {"emoji": "🎣", "label": "Dhyan do!", "color": "#e8f4f8", "border": "#3498db"},
    "SAMJHAO": {"emoji": "📖", "label": "Samjho",   "color": "#eafaf1", "border": "#27ae60"},
    "MISAAL":  {"emoji": "🏏", "label": "Misaal",   "color": "#fef9e7", "border": "#f39c12"},
    "KARO":    {"emoji": "✋", "label": "Karo!",    "color": "#f5eef8", "border": "#9b59b6"},
    "SAWAAL":  {"emoji": "❓", "label": "Sawaal",   "color": "#fdedec", "border": "#e74c3c"},
}

# One quick checkpoint question per section (grade-appropriate)
CHECKPOINT_PROMPTS = {
    "HOOK":    "Is kahani / sawaal ke baare mein ek aasaan MCQ sawaal banao (4 options a/b/c/d). JSON only: {\"q\":\"...\",\"a\":\"...\",\"b\":\"...\",\"c\":\"...\",\"d\":\"...\",\"correct\":\"a\",\"hint\":\"...\"}",
    "SAMJHAO": "Abhi jo concept samjhaya gaya us par ek check sawaal banao. JSON only: {\"q\":\"...\",\"a\":\"...\",\"b\":\"...\",\"c\":\"...\",\"d\":\"...\",\"correct\":\"b\",\"hint\":\"...\"}",
    "MISAAL":  "Is Pakistani misaal se ek sawaal banao. JSON only: {\"q\":\"...\",\"a\":\"...\",\"b\":\"...\",\"c\":\"...\",\"d\":\"...\",\"correct\":\"c\",\"hint\":\"...\"}",
    "KARO":    "Is activity ke baare mein ek sawaal banao. JSON only: {\"q\":\"...\",\"a\":\"...\",\"b\":\"...\",\"c\":\"...\",\"d\":\"...\",\"correct\":\"a\",\"hint\":\"...\"}",
}

CHECKPOINT_CACHE_FILE = _data("checkpoint_cache.json")

def load_checkpoint_cache():
    if os.path.exists(CHECKPOINT_CACHE_FILE):
        with open(CHECKPOINT_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_checkpoint_cache(data):
    with open(CHECKPOINT_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_cache_files():
    """Create empty cache files if they don't exist — prevents missing file errors."""
    for fname in [QUIZ_CACHE_FILE, CHECKPOINT_CACHE_FILE, JUMA_TEST_FILE]:
        if not os.path.exists(fname):
            with open(fname, "w", encoding="utf-8") as f:
                json.dump({}, f)

# Initialize caches on startup
ensure_cache_files()

# ---------------------------------------------------------------------------
# FILL IN THE BLANK — Mode 1 written answers
# ---------------------------------------------------------------------------
FITB_CACHE_FILE = _data("fitb_cache.json")
FITB_GENERATE_PROMPT = BRAND + """
ROLE: Examiner Sahib. Grade {grade} ke liye fill-in-the-blank sawaal banao.
Topic: {topic}
Content (se sawaal lo): {content}

ROMAN URDU ONLY. Pakistani examples use karo.
3 chhote fill-in-the-blank sawaal banao — hر mein ek blank (___) ho.
Blank ka jawab 1-3 alfaaz ka ho. Aasaan aur clear ho.

ONLY valid JSON respond karo:
{{"blanks":[
  {{"sentence":"Podha _____ se khana banata hai.","answer":"suraj","synonyms":["roshni","dhoop","sunlight"],"hint":"Roz subah aasaman mein kya chamakta hai?"}},
  {{"sentence":"...","answer":"...","synonyms":["..."],"hint":"..."}},
  {{"sentence":"...","answer":"...","synonyms":["..."],"hint":"..."}}
]}}

Rules:
- EXACTLY 3 blanks
- answer = sab se common jawab (1-2 alfaaz)
- synonyms = aur qabil qabool jawab (2-4 words)
- hint = ek chhota sa hint agar bachay ko mushkil ho
- Roman Urdu mein
- NO text outside JSON
"""

FITB_CHECK_PROMPT = BRAND + """
ROLE: Class Teacher — friendly checker.
Grade {grade} ka bachay ne fill-in-the-blank ka jawab diya hai.

Sawaal: {sentence}
Sahi jawab: {answer}
Qabil qabool aur jawab: {synonyms}
Bachay ka jawab: {student_answer}

Kya bachay ka jawab sahi hai? Exact match zaroori nahi — matlab sahi ho to sahi hai.
Spelling galat ho to bhi jawab sahi ho sakta hai agar concept sahi hai.

ONLY JSON respond karo:
{{"correct": true/false, "message": "Roman Urdu mein pyaar se feedback (1 jumla)", "stars": 1}}
"""

def load_fitb_cache():
    if os.path.exists(FITB_CACHE_FILE):
        with open(FITB_CACHE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_fitb_cache(data):
    with open(FITB_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_fitb_questions(topic, grade, content):
    """Get or generate fill-in-the-blank questions for a topic."""
    cache = load_fitb_cache()
    key = f"{topic}_{grade}"
    if key in cache:
        return cache[key]
    prompt = FITB_GENERATE_PROMPT.format(
        grade=grade, topic=topic,
        content=content[:1000]
    )
    try:
        raw = run_agent(BRAND, prompt, 800)
        data = parse_json(raw)
        if "blanks" in data and len(data["blanks"]) > 0:
            cache[key] = data["blanks"]
            save_fitb_cache(cache)
            return data["blanks"]
    except:
        pass
    return []

def check_fitb_answer(sentence, answer, synonyms, student_answer, grade):
    """Check if student's fill-in-the-blank answer is correct.
    Uses local logic first (free), caches AI results (never pays twice)."""
    s = student_answer.strip().lower()

    # Too short = reject immediately
    if len(s) <= 1:
        return {"correct": False,
                "message": "Thoda aur likho — ek harf se jawab nahi hota!",
                "stars": 0}

    correct_words = [answer.strip().lower()] + [x.strip().lower() for x in synonyms if x.strip()]

    # Exact match
    if s in correct_words:
        return {"correct": True, "message": "Shabash! Bilkul sahi! ⭐", "stars": 1}

    # Fuzzy match — word must be ≥3 chars and ≥70% overlap
    for w in correct_words:
        if not w or len(w) < 2: continue
        if len(s) >= 3 and len(w) >= 3:
            shorter = min(len(s), len(w))
            longer = max(len(s), len(w))
            if s.startswith(w[:max(3, len(w)-1)]) or w.startswith(s[:max(3, len(s)-1)]):
                if shorter / longer >= 0.70:
                    return {"correct": True,
                            "message": "Sahi hai! Spelling thodi alag thi lekin matlab sahi! ⭐",
                            "stars": 1}

    # Check FITB answer cache before calling AI
    if len(s) >= 2:
        fitb_ans_cache = load_fitb_cache()
        cache_k = f"check_{answer}_{s}"
        if cache_k in fitb_ans_cache:
            return fitb_ans_cache[cache_k]
        try:
            prompt = FITB_CHECK_PROMPT.format(
                grade=grade, sentence=sentence,
                answer=answer, synonyms=", ".join(synonyms),
                student_answer=student_answer
            )
            raw = run_agent(BRAND, prompt, 300)
            result = parse_json(raw)
            # Cache this result so same answer never costs twice
            fitb_ans_cache[cache_k] = result
            save_fitb_cache(fitb_ans_cache)
            return result
        except:
            pass

    return {"correct": False,
            "message": "Dobara koshish karo — sahi jawab soch ke likho!",
            "stars": 0}


# ---------------------------------------------------------------------------
# HOMEWORK DIARY
# ---------------------------------------------------------------------------
HW_FILE = _data("homework_diary.json")

HW_TYPES = {
    "low": [
        "Ghar mein 5 cheezein dhundho jo {topic} se milti hon — ammi/abu ko dikhao",
        "Ek tasveer banao: {topic} kya hai — rang bhi bharo",
        "Raat ko ammi/abu ko batao: aaj {topic} ke baare mein kya seekha?",
        "3 baar zor se parho: '{key_word}' — phir khud likhne ki koshish karo",
    ],
    "mid": [
        "Ek jumla likho apne alfaaz mein: '{topic}' kya hota hai?",
        "Ghar mein {topic} ka ek real misaal dhundho — kal batana hai",
        "Ammi/abu se pucho: unhe {topic} ke baare mein kya pata hai?",
        "Notebook mein {topic} ka chhota sa diagram banao",
    ],
    "high": [
        "Ek paragraph likho: {topic} zindagi mein kahan kaam aata hai?",
        "{topic} ka ek Pakistani example dhundho — internet ya ghar se",
        "3 dost ya bhai-behen ko {topic} samjhao — kal batao unhone kya samjha",
        "Notebook mein likho: {topic} ki 3 important baatein",
    ],
}

def get_hw_band(grade):
    if grade <= 2: return "low"
    elif grade <= 4: return "mid"
    return "high"

def load_hw_diary():
    if os.path.exists(HW_FILE):
        with open(HW_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_hw_diary(data):
    with open(HW_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def assign_homework(roll, grade, topic, subject_name):
    import random
    band = get_hw_band(grade)
    template = random.choice(HW_TYPES[band])
    hw_text = template.format(
        topic=topic,
        key_word=topic.split()[0] if topic else topic,
    )
    diary = load_hw_diary()
    key = str(roll)
    if key not in diary: diary[key] = []
    if not any(e["date"] == today() for e in diary[key]):
        entry = {"date": today(), "topic": topic, "subject": subject_name,
                 "task": hw_text, "done": False, "done_date": None}
        diary[key].append(entry)
        save_hw_diary(diary)
        return entry
    return None

def get_pending_homework(roll):
    diary = load_hw_diary()
    today_d = datetime.date.today()
    pending = []
    for e in diary.get(str(roll), []):
        if e.get("done"): continue
        age = (today_d - datetime.date.fromisoformat(e["date"])).days
        if 1 <= age <= 3:
            pending.append(e)
    return pending

def get_todays_homework(roll):
    diary = load_hw_diary()
    return [e for e in diary.get(str(roll), []) if e["date"] == today()]

def mark_hw_done(roll, hw_date):
    diary = load_hw_diary()
    for e in diary.get(str(roll), []):
        if e["date"] == hw_date and not e.get("done"):
            e["done"] = True
            e["done_date"] = today()
    save_hw_diary(diary)


def get_checkpoint_question(topic, section, section_text, grade):
    """Generate or retrieve a checkpoint MCQ for a lesson section."""
    ck = load_checkpoint_cache()
    ck_key = f"{topic}_{section}_{grade}"
    if ck_key in ck:
        return ck[ck_key]
    prompt = (
        f"Tum Grade {grade} ke liye ek Roman Urdu checkpoint sawaal banao.\n"
        f"Topic: {topic}\nSection: {section}\n\nSection content:\n{section_text[:600]}\n\n"
        f"{CHECKPOINT_PROMPTS.get(section, CHECKPOINT_PROMPTS['SAMJHAO'])}"
    )
    try:
        raw = run_agent(MCQ_EXAMINER_PROMPT, prompt, 500)
        q = parse_json(raw)
        if "q" in q and "correct" in q:
            ck[ck_key] = q
            save_checkpoint_cache(ck)
            return q
    except:
        pass
    return None

def parse_lesson_sections(content):
    """Split lesson text into ordered sections by ## headings."""
    import re
    sections = []
    # Handle both \n## and content starting with ##
    # Normalize: ensure content starts without leading ##
    content = content.strip()
    # Split on ## headings (handles both \n## and start-of-string ##)
    parts = re.split(r'(?:^|\n)##\s+', content)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.split('\n', 1)
        raw_heading = lines[0].strip()
        # Remove any leftover ## prefix
        heading = raw_heading.lstrip('#').strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        # Match known section names
        heading_upper = heading.upper()
        matched = None
        for key in SECTION_META:
            if key in heading_upper:
                matched = key
                break
        sections.append({
            "key": matched or "SAMJHAO",
            "heading": heading,
            "body": body
        })
    return sections if sections else [{"key": "SAMJHAO", "heading": "Sabaq", "body": content}]

def render_lesson_with_checkpoints(content, topic, subject_key, grade, student):
    """Render lesson section by section with a checkpoint MCQ after each."""
    sections = parse_lesson_sections(content)
    ck_state = st.session_state.setdefault("checkpoints", {})
    topic_key = f"{subject_key}_{topic}_{grade}"
    if topic_key not in ck_state:
        ck_state[topic_key] = {}

    all_unlocked = True
    for i, sec in enumerate(sections):
        meta = SECTION_META.get(sec["key"], SECTION_META["SAMJHAO"])
        sec_id = f"{topic_key}_sec{i}"
        answered = ck_state[topic_key].get(sec_id, {}).get("answered", False)

        # Show section only if previous checkpoint passed (or first section)
        prev_answered = i == 0 or ck_state[topic_key].get(f"{topic_key}_sec{i-1}", {}).get("answered", False)

        if not prev_answered:
            st.markdown(
                f'<div style="text-align:center;padding:14px;background:#f8f9fa;'
                f'border-radius:10px;border:2px dashed #bdc3c7;color:#888;margin:8px 0">'
                f'🔒 Pehle upar wala sawaal sahi karo — phir agla hissa khulay ga!'
                f'</div>', unsafe_allow_html=True)
            all_unlocked = False
            break

        # Render the section box
        st.markdown(
            f'<div style="padding:14px 18px;background:{meta["color"]};'
            f'border-left:5px solid {meta["border"]};border-radius:0 10px 10px 0;margin:10px 0">'
            f'<p style="font-size:0.82em;font-weight:700;color:{meta["border"]};margin:0">'
            f'{meta["emoji"]} {sec["heading"]}</p>'
            f'<div style="margin-top:6px">{sec["body"].replace(chr(10),"<br>")}</div>'
            f'</div>', unsafe_allow_html=True)

        # No checkpoint needed after the last section (SAWAAL) — it's already questions
        if sec["key"] == "SAWAAL" or i == len(sections) - 1:
            continue

        # Checkpoint question
        if answered:
            was_right = ck_state[topic_key].get(sec_id, {}).get("right", False)
            st.markdown(
                f'<div style="padding:8px 14px;background:{"#eafaf1" if was_right else "#fdecea"};'
                f'border-radius:8px;border:1px solid {"#27ae60" if was_right else "#e74c3c"};'
                f'margin:4px 0;font-size:0.9em">'
                f'{"✅ Sahi! Aage barhain!" if was_right else "✅ Dekha! Aage chalein"}'
                f'</div>', unsafe_allow_html=True)
        else:
            # Try to load from cache first, then generate
            ck_q = get_checkpoint_question(topic, sec["key"], sec["body"], grade)
            if ck_q:
                with st.container():
                    st.markdown(
                        f'<div style="padding:12px 16px;background:#fff8e1;border-radius:10px;'
                        f'border:2px solid {meta["border"]};margin:8px 0">'
                        f'<p style="font-size:0.82em;color:{meta["border"]};margin:0 0 4px 0">'
                        f'🤔 Checkpoint sawaal — jawab do phir aage barhein!</p>'
                        f'<b>{ck_q["q"]}</b></div>', unsafe_allow_html=True)
                    if ck_q.get("hint"):
                        st.caption(f"💡 Hint: {ck_q['hint']}")
                    correct = ck_q.get("correct","a").lower()
                    ck_cols = st.columns(2)
                    opted = False
                    for ki, (opt_key, opt_emoji) in enumerate([("a","🔵"),("b","🟢"),("c","🟡"),("d","🔴")]):
                        opt_text = ck_q.get(opt_key,"")
                        col = ck_cols[ki % 2]
                        if col.button(f"{opt_emoji} {opt_key.upper()}: {opt_text}",
                                      key=f"ck_{sec_id}_{opt_key}", width='stretch'):
                            is_right = opt_key == correct
                            ck_state[topic_key][sec_id] = {"answered": True, "right": is_right}
                            if is_right:
                                # +1 star for correct checkpoint
                                reg_ck = load_register()
                                for s in reg_ck["students"]:
                                    if s["roll"] == student["roll"]:
                                        s["stars"] += 1; save_register(reg_ck); break
                            opted = True
                            st.rerun()
                    if not opted:
                        all_unlocked = False
                        break
            else:
                # No checkpoint question available — just auto-unlock
                ck_state[topic_key][sec_id] = {"answered": True, "right": True}

    return all_unlocked


# =====================================================================
#  SIMPLE MODE AUDIO (Grade 1-2)  — cache-first TTS, autoplay
# =====================================================================
TTS_CACHE_DIR = _data("tts_cache")
TTS_MODEL = ai_config.TTS_MODEL      # ai_config.json se
TTS_VOICE = ai_config.TTS_VOICE

def get_tts_mp3(text):
    """Return MP3 bytes for `text`, cache-first. Generates via OpenAI TTS only
    if not already on disk, then caches. Returns None on any failure."""
    import hashlib
    if not text or not text.strip():
        return None
    os.makedirs(TTS_CACHE_DIR, exist_ok=True)
    key = hashlib.md5(text.strip().encode("utf-8")).hexdigest()
    path = os.path.join(TTS_CACHE_DIR, f"{key}.mp3")
    if os.path.exists(path):                       # CACHE HIT — zero API cost
        with open(path, "rb") as f:
            return f.read()
    if not AI_ENABLED or not ai_config.TTS_ENABLED:  # KB Mode ya TTS band
        return None                                  # -> browser awaaz fallback
    try:                                           # CACHE MISS — one API call
        resp = ai_config.get_tts_client().audio.speech.create(
            model=TTS_MODEL, voice=TTS_VOICE, input=text.strip())
        audio = resp.read() if hasattr(resp, "read") else resp.content
        with open(path, "wb") as f:
            f.write(audio)
        return audio
    except Exception:
        return None

def autoplay_tts(text):
    """Play the lesson audio (SIMPLE mode only).

    Uses an <audio autoplay> tag rendered inside components.html so the
    accompanying <script> actually runs (st.markdown strips scripts). A unique
    nonce forces a brand-new element on every call, so 'Phir Suno' reliably
    REPLAYS (autoplay only fires on a freshly-inserted element). Explicit
    .play() covers the case where autoplay is gated but a user gesture is active.
    Falls back to browser speech synthesis if TTS audio is unavailable."""
    import base64
    import streamlit.components.v1 as components
    nonce = st.session_state.get("_tts_nonce", 0) + 1
    st.session_state["_tts_nonce"] = nonce
    mp3 = get_tts_mp3(text)
    if mp3:
        b64 = base64.b64encode(mp3).decode("ascii")
        components.html(
            f'''<audio id="tts{nonce}" autoplay>
  <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
</audio>
<script>
  (function(){{
    var a = document.getElementById("tts{nonce}");
    if (a) {{ a.muted = false; var p = a.play(); if (p && p.catch) p.catch(function(e){{}}); }}
  }})();
</script>''',
            height=0,
        )
    else:
        # Fallback: browser speech synthesis (Hindi voice reads Roman Urdu well)
        safe = (text or "").replace("\\", " ").replace('"', " ").replace("\n", " ")
        components.html(
            f'''<script>
  (function(){{try{{
    var u = new SpeechSynthesisUtterance("{safe}");
    u.lang = "hi-IN"; u.rate = 0.9;
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(u);
  }}catch(e){{}}}})();
</script>''',
            height=0,
        )


# =====================================================================
#  SIMPLE MODE RENDERERS (Grade 1-2)  — additive, no checkpoints/typing
# =====================================================================
def render_simple_lesson(sk, grade, topic_title, student, subj):
    """Big emoji, short Roman-Urdu text, audio autoplay, max 2 buttons.
    Returns 'quiz' when the child taps 'Ho Gaya', else None."""
    topic = load_kb_topic_full(sk, grade, topic_title) or {}
    emoji = topic.get("emoji") or subj.get("emoji") or "🌟"
    text_simple = topic.get("text_simple") or simple_text_fallback(topic.get("lesson", ""))
    audio_text = topic.get("audio_text") or text_simple

    # Audio autoplay on first load of this topic (SIMPLE only) — Step 6 hook
    if st.session_state.get("simple_audio_topic") != topic_title:
        st.session_state.simple_audio_topic = topic_title
        st.session_state.simple_play_audio = True
    if st.session_state.get("simple_play_audio") and "autoplay_tts" in globals():
        autoplay_tts(audio_text)
        st.session_state.simple_play_audio = False

    # Lesson ki tasveer (agar bani hui hai) — warna bara emoji
    _img = lesson_image_path(grade, sk, topic_title)
    if _img:
        ic1, ic2, ic3 = st.columns([1, 3, 1])
        with ic2:
            st.image(_img, width='stretch')

    # Big emoji (sirf jab tasveer na ho) + big text card
    _emoji_html = ("" if _img else
                   f'<div style="font-size:80px;line-height:1.1">{emoji}</div>')
    st.markdown(
        f'<div style="text-align:center;padding:24px 16px;background:#fffef7;'
        f'border:3px solid {subj.get("border", "#f39c12")};border-radius:24px;margin:8px 0">'
        f'{_emoji_html}'
        f'<div style="font-size:32px;line-height:1.5;font-weight:700;color:#2c3e50;'
        f'margin-top:12px">{text_simple}</div>'
        f'</div>', unsafe_allow_html=True)

    # Hand-drawn teaching picture (fractions/ghadi/ginti...) — free, no API
    _vis = get_topic_visual(sk, grade, topic_title)
    if _vis:
        st.markdown(_vis, unsafe_allow_html=True)
    render_money_photos(topic_title)   # asli note ki photos, agar rakhi hon

    # Max 2 buttons
    result = None
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🔊 Phir Suno", width='stretch',
                     key=f"simple_hear_{sk}_{topic_title}"):
            st.session_state.simple_play_audio = True
            st.rerun()
    with b2:
        if st.button("✅ Ho Gaya!", width='stretch', type="primary",
                     key=f"simple_done_{sk}_{topic_title}"):
            result = "quiz"
    return result


DEFAULT_OPT_EMOJIS = ["🍎", "🌸", "🚗", "🐤"]

def build_simple_quiz(sk, grade, topic_title):
    """Return a list of SIMPLE quiz questions.
    Uses the KB 'simple_quiz' field if present (Step 5); else derives a single
    3-option question from the standard KB quiz so SIMPLE works pre-enrichment."""
    topic = load_kb_topic_full(sk, grade, topic_title) or {}
    sq = topic.get("simple_quiz")
    if sq:
        return sq
    # Fallback: build one 3-option question from the first KB quiz question
    quiz = topic.get("quiz") or {}
    qs = quiz.get("questions") or []
    if not qs:
        return []
    q0 = qs[0]
    correct_letter = str(q0.get("correct", "a")).strip().lower()
    correct_text = q0.get(correct_letter, "Sahi jawab")
    distractors = [q0.get(l) for l in ("a", "b", "c", "d")
                   if l != correct_letter and q0.get(l)]
    opts_text = [correct_text] + distractors[:2]
    import random as _r
    order = list(range(len(opts_text)))
    _r.Random(hash(topic_title) & 0xffff).shuffle(order)
    options = []
    ans_idx = 0
    for new_i, orig_i in enumerate(order):
        options.append({"emoji": DEFAULT_OPT_EMOJIS[new_i % len(DEFAULT_OPT_EMOJIS)],
                        "text": opts_text[orig_i]})
        if orig_i == 0:
            ans_idx = new_i
    return [{"emoji": "❓",
             "question_short": q0.get("q", "Sawaal"),
             "options": options,
             "answer": ans_idx}]


def render_simple_quiz(sk, grade, topic_title, student, subj):
    """3 emoji-button options, zero typing. Correct -> balloons + star.
    Wrong -> encourage + re-show. Wrong answers NEVER write to Ghalti Copy."""
    quiz = build_simple_quiz(sk, grade, topic_title)
    if not quiz:
        st.info("🎉 Sabaq mukammal! Shabash!")
        if st.button("⬅️ Wapas hallway", width='stretch',
                     key=f"sq_none_back_{sk}"):
            go(screen="hallway")
            st.session_state.lesson_result = None
            st.session_state.show_simple_quiz = False
            st.rerun()
        return

    idx = st.session_state.get("simple_quiz_idx", 0)
    if idx >= len(quiz):
        # All questions done
        st.balloons()
        st.markdown(
            '<div style="text-align:center;padding:24px;background:#eafaf1;'
            'border:3px solid #27ae60;border-radius:24px">'
            '<div style="font-size:64px">🌟🎉🌟</div>'
            '<div style="font-size:28px;font-weight:700;color:#27ae60">Shabash! Sab sahi!</div>'
            '</div>', unsafe_allow_html=True)
        if st.button("⬅️ Wapas hallway", width='stretch', type="primary",
                     key=f"sq_done_back_{sk}"):
            # Mark topic done so it unlocks the next one (same as STANDARD)
            mark_topic_done(student["roll"], sk, topic_title)
            go(screen="hallway")
            st.session_state.lesson_result = None
            st.session_state.show_simple_quiz = False
            st.session_state.simple_quiz_idx = 0
            st.rerun()
        return

    q = quiz[idx]
    q_emoji = q.get("emoji", "❓")
    q_text = q.get("question_short", "Sawaal")
    options = q.get("options", [])
    answer = q.get("answer", 0)

    st.markdown(
        f'<div style="text-align:center;padding:20px;background:#fef9f0;'
        f'border:3px solid {subj.get("border", "#f39c12")};border-radius:24px;margin:8px 0">'
        f'<div style="font-size:56px">{q_emoji}</div>'
        f'<div style="font-size:28px;font-weight:700;color:#2c3e50;margin-top:8px">{q_text}</div>'
        f'</div>', unsafe_allow_html=True)

    # 3 big emoji-button options
    cols = st.columns(len(options) if options else 1)
    for oi, opt in enumerate(options):
        with cols[oi]:
            label = f"{opt.get('emoji','')}\n\n{opt.get('text','')}"
            if st.button(label, width='stretch',
                         key=f"sq_{sk}_{topic_title}_{idx}_{oi}"):
                if oi == answer:
                    st.session_state[f"sq_feedback_{idx}"] = "right"
                    # +1 star for correct (encouragement)
                    reg_q = load_register()
                    for s in reg_q["students"]:
                        if s["roll"] == student["roll"]:
                            s["stars"] += 1; save_register(reg_q); break
                    st.session_state.simple_quiz_idx = idx + 1
                else:
                    # Wrong: encourage, re-show. NO Ghalti Copy write in SIMPLE.
                    st.session_state[f"sq_feedback_{idx}"] = "wrong"
                st.rerun()

    fb = st.session_state.get(f"sq_feedback_{idx}")
    if fb == "wrong":
        st.markdown(
            '<div style="text-align:center;font-size:22px;font-weight:700;color:#e67e22;'
            'padding:12px">Koshish acchi thi! Dobara try karo 💪</div>',
            unsafe_allow_html=True)


import streamlit as st

st.set_page_config(page_title="AI4Kids.pk", page_icon="🐱", layout="wide")

# ===========================================================================
# SCHOOL DARWAZA — PASSWORD GATE
# ---------------------------------------------------------------------------
# Password environment variables se aata hai (Railway -> Variables).
# Code mein kabhi password na likhein — warna GitHub par chala jaayega.
#
#   AI4KIDS_SCHOOL_PASSWORD  -> poore school ka password
#   AI4KIDS_ADMIN_PASSWORD   -> sirf Admin office ka alag password
#
# PC par yeh set nahi hote -> koi password nahi poocha jaata -> pehle jaisa.
# ===========================================================================
def _secret(name):
    """Password dhoondo: pehle Streamlit Secrets, phir environment variable.
    Dono jagah na mile to khali — yaani PC par koi password nahi poocha jaata."""
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return os.environ.get(name, "").strip()


SCHOOL_PASSWORD = _secret("AI4KIDS_SCHOOL_PASSWORD")
ADMIN_PASSWORD  = _secret("AI4KIDS_ADMIN_PASSWORD")


def _school_gate():
    """Agar school password set hai to andar aane se pehle poocho."""
    if not SCHOOL_PASSWORD:
        return                                   # PC mode — khula hai
    if st.session_state.get("gate_ok"):
        return                                   # pehle hi andar aa chuke

    st.markdown(
        '<div style="text-align:center;padding:26px 16px;background:linear-gradient(135deg,#fef9e7,#eafaf1);'
        'border-radius:18px;border:3px solid #f39c12;margin-bottom:18px">'
        '<h1>🐱 AI4Kids.pk</h1>'
        '<p style="font-size:1.15em;margin:0">اسلام آباد کا پہلا اردو AI سکول</p>'
        '<p style="font-size:1.05em;margin-top:10px">🔒 School band hai — password daal kar andar aayein</p>'
        '</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        pw = st.text_input("School ka password", type="password",
                           key="gate_pw", label_visibility="collapsed",
                           placeholder="School ka password likhein")
        if st.button("🚪 Andar aao", width='stretch', type="primary"):
            if pw == SCHOOL_PASSWORD:
                st.session_state.gate_ok = True
                st.rerun()
            else:
                st.error("❌ Password ghalat hai — dobara koshish karein.")
        st.caption("Yeh school sirf AI4Kids ke students aur unke walidain ke liye hai.")
    st.stop()


# ===== DEVICE-LOCKED ACCESS CODES =====
_DEVICE_LOCK = False
_DL_ERR = None
try:
    import device_lock
    _DEVICE_LOCK = device_lock.is_configured()
    if not _DEVICE_LOCK:
        _DL_ERR = "is_configured() = False (secrets nahi mile)"
except Exception as _e:
    import traceback as _tb
    _DL_ERR = _tb.format_exc()

if _DL_ERR:
    st.error("⚠️ DEVICE LOCK OFF — wajah:")
    st.code(_DL_ERR)

if _DEVICE_LOCK:
    if not device_lock.login_gate():
        st.stop()
    if st.session_state.get("ai4k_admin"):
        with st.sidebar:
            st.success("👑 Admin mode")
            _show = st.checkbox("🔑 Access Codes panel")
        if _show:
            import admin_codes
            admin_codes.render()
            st.stop()
else:
    _school_gate()

st.markdown("""<style>.block-container{max-width:100% !important;padding-left:2rem !important;padding-right:2rem !important;}</style>""", unsafe_allow_html=True)
st.markdown("""<style>
.stButton>button{font-size:1.12rem !important;padding:0.6rem 1rem !important;border-radius:14px !important;font-weight:700 !important;}
p, li{font-size:1.05rem;}
.stTabs [data-baseweb="tab"]{font-size:1.05rem;font-weight:700;}
.st-key-urdu_sum_btn button{background:#8e44ad !important;color:#fff !important;border:none !important;font-size:1.15rem !important;padding:0.7rem !important;}
.st-key-urdu_sum_btn button:hover{background:#7d3c98 !important;color:#fff !important;}
.st-key-urdu_sum_btn button p{color:#fff !important;font-weight:700 !important;}
</style>""", unsafe_allow_html=True)

for k, v in [("mode","door"),("stu_roll",None),("stu_screen","assembly"),
             ("stu_subject",None),("lesson_result",None),("quiz_result",None),
             ("chat_history",[]),("messages",[]),("assembly_done",False),
             ("mcq_questions",None),("mcq_current",0),("mcq_answers",[]),
             ("mcq_done",False),("mcq_topic",""),
             ("lessons_today",0),("quizzes_today",0),("stars_today",0),
             ("celebration",None),("show_video",False),("urdu_summary",None),
             ("ghalti_mode",False),("ghalti_idx",0),("ghalti_answers",[]),
             ("juma_questions",None),("juma_current",0),("juma_answers",[]),
             ("juma_done",False),("checkpoints",{}),
             ("fitb_questions",[]),("fitb_results",{}),("fitb_loaded_topic",""),
             ("ui_mode","STANDARD"),("simple_quiz_idx",0),
             ("show_simple_quiz",False),("simple_audio_topic",None),
             ("simple_play_audio",False)]:
    if k not in st.session_state: st.session_state[k] = v

def go(mode=None, screen=None, roll=None, subject=None):
    if mode: st.session_state.mode = mode
    if screen: st.session_state.stu_screen = screen
    if roll is not None: st.session_state.stu_roll = roll
    if subject is not None: st.session_state.stu_subject = subject
    st.session_state.scroll_top = True

def scroll_to_top():
    """Scroll page to top after screen change."""
    if st.session_state.get("scroll_top"):
        st.session_state.scroll_top = False
        import streamlit.components.v1 as components
        components.html(
            """<script>
            const doc = window.parent.document;
            doc.querySelectorAll('section.main, [data-testid="stAppViewContainer"], [data-testid="stMain"]')
               .forEach(el => el.scrollTo({top: 0, behavior: "instant"}));
            window.parent.scrollTo({top: 0, behavior: "instant"});
            </script>""",
            height=0,
        )

def reset_mcq():
    st.session_state.mcq_questions = None
    st.session_state.mcq_current = 0
    st.session_state.mcq_answers = []
    st.session_state.mcq_done = False
    st.session_state.mcq_topic = ""

def reset_student_session():
    """Log the current student OUT and clear all per-student state, so the next
    child gets the name-picker instead of the previous student's session.
    (Note: go(roll=None) cannot do this — go() ignores a None roll by design.)"""
    st.session_state.stu_roll = None
    st.session_state.stu_screen = "assembly"
    st.session_state.assembly_done = False
    st.session_state.lesson_result = None
    st.session_state.quiz_result = None
    st.session_state.chat_history = []
    st.session_state.messages = []
    st.session_state.urdu_summary = None
    st.session_state.show_video = False
    st.session_state.checkpoints = {}
    st.session_state.fitb_questions = []
    st.session_state.fitb_results = {}
    st.session_state.fitb_loaded_topic = ""
    st.session_state.ghalti_mode = False
    st.session_state.ghalti_idx = 0
    st.session_state.ghalti_answers = []
    st.session_state.juma_questions = None
    st.session_state.juma_current = 0
    st.session_state.juma_answers = []
    st.session_state.juma_done = False
    st.session_state.celebration = None
    # SIMPLE mode (Grade 1-2) state
    st.session_state.ui_mode = "STANDARD"
    st.session_state.show_simple_quiz = False
    st.session_state.simple_audio_topic = None
    st.session_state.simple_play_audio = False
    st.session_state.simple_quiz_idx = 0
    reset_mcq()

def mcq_answer(choice, correct, qi):
    st.session_state.mcq_answers.append({"chose": choice, "correct": correct, "right": choice == correct, "qi": qi})
    if st.session_state.mcq_current < 4:
        st.session_state.mcq_current += 1
    else:
        st.session_state.mcq_done = True

def do_admit():
    name = st.session_state.get("adm_name","")
    grade = st.session_state.get("adm_grade",1)
    if name.strip():
        s = admit_student(load_register(), name, grade)
        st.session_state.admit_msg = f"Mubarak! {s['name']} — Roll {s['roll']}, Grade {s['grade']} {s['section']}"

def do_edit(roll):
    reg = load_register()
    for s in reg["students"]:
        if s["roll"] == roll:
            nm = st.session_state.get(f"e_name_{roll}","").strip()
            if nm: s["name"] = nm.title()
            st.session_state.edit_msg = f"✅ Saved: {s['name']}"
    save_register(reg)

def set_grade(roll, grade):
    reg = load_register()
    for s in reg["students"]:
        if s["roll"] == roll:
            s["grade"] = grade
            st.session_state.edit_msg = f"✅ {s['name']} ab Grade {grade}!"
    save_register(reg)

def set_section(roll, sec):
    reg = load_register()
    for s in reg["students"]:
        if s["roll"] == roll:
            s["section"] = sec
            st.session_state.edit_msg = f"✅ {s['name']} ab {sec} Section!"
    save_register(reg)

def delete_student(roll):
    reg = load_register()
    reg["students"] = [s for s in reg["students"] if s["roll"] != roll]
    save_register(reg)
    st.session_state.edit_msg = f"🗑️ Roll {roll} delete ho gaya!"


# BANNER — only on Main Door, Assembly, and Admin (hidden inside school to save scroll)
_inside_school = (
    st.session_state.mode == "student"
    and st.session_state.stu_roll is not None
    and st.session_state.stu_screen not in ("assembly",)
)
if not _inside_school:
    if os.path.exists(_app("banner.png")):
        c1,c2,c3 = st.columns([1,2,1])
        c2.image(_app("banner.png"), width='stretch')
        st.markdown('<p style="text-align:center">اسلام آباد کا پہلا اردو AI سکول — Chalo Seekhte Hain!</p>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center"><h1>🐱 AI4Kids.pk</h1><p>اسلام آباد کا پہلا اردو AI سکول</p></div>', unsafe_allow_html=True)

register = load_register()

# ---------- Lesson Bank (HTML app with SNC curriculum + video library) ----------
LESSON_BANK_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lesson_bank.html")
CURRICULUM_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "curriculum.html")

def open_lesson_bank():
    # Cloud par koi desktop browser nahi hota — chup chaap nazarandaz kar do,
    # app phir bhi HTML ko andar iframe mein dikha deta hai.
    try:
        import webbrowser
        webbrowser.open("file:///" + LESSON_BANK_PATH.replace("\\", "/"))
    except Exception:
        pass

def open_curriculum():
    try:
        import webbrowser
        webbrowser.open("file:///" + CURRICULUM_PATH.replace("\\", "/"))
    except Exception:
        pass

def render_html_viewers():
    """Render the Curriculum / Lesson Bank HTML INSIDE the app when toggled.
    Browsers block file:// links opened from an http page, so we embed the
    HTML in a sandboxed iframe instead of linking to the file."""
    import streamlit.components.v1 as components
    if st.session_state.get("view_curriculum"):
        st.markdown("#### 📖 Curriculum — Class 1-5 (FBISE/SNC)")
        if st.button("✖️ Curriculum band karo", key="cur_close_top"):
            st.session_state.view_curriculum = False; st.rerun()
        try:
            components.html(open(CURRICULUM_PATH, encoding="utf-8").read(),
                            height=650, scrolling=True)
        except Exception as e:
            st.error(f"Curriculum nahi khul saki: {e}")
    if st.session_state.get("view_lessonbank"):
        st.markdown("#### 📚 Lesson Bank")
        st.caption("Agar Streamlit Fork page dikhe to in-app close / refresh use karein.")
        if st.button("✖️ Lesson Bank band karo", key="lb_close_top"):
            st.session_state.view_lessonbank = False; st.rerun()
        try:
            components.html(open(LESSON_BANK_PATH, encoding="utf-8").read(),
                            height=900, scrolling=True)
        except Exception as e:
            st.error(f"Lesson Bank nahi khul saki: {e}")


# ---------- Curriculum link + topic progress helpers ----------
CURR_SUBJ_MAP = {"ai": "Computing & AI", "robotics": "Computing & AI",
                 "english": "English", "math": "Math", "science": "Science"}

def load_curriculum():
    """SNC/FBISE curriculum parsed from lesson_bank.html (single source of truth)."""
    if "curriculum_data" not in st.session_state:
        import re as _re
        try:
            _src = open(LESSON_BANK_PATH, encoding="utf-8").read()
            _m = _re.search(r"const CURRICULUM = (\{.*?\n\});", _src, _re.S)
            st.session_state.curriculum_data = json.loads(_m.group(1)) if _m else {}
        except Exception:
            st.session_state.curriculum_data = {}
    return st.session_state.curriculum_data

def get_curriculum_topics(subject_key, grade):
    g = min(max(int(grade), 1), 5)
    return load_curriculum().get("Grade %d" % g, {}).get(CURR_SUBJ_MAP.get(subject_key, ""), [])

def get_done_topics(student, subject_key):
    return student.get("done_topics", {}).get(subject_key, [])

def mark_topic_done(roll, subject_key, topic):
    reg = load_register()
    for s in reg["students"]:
        if s["roll"] == roll:
            lst = s.setdefault("done_topics", {}).setdefault(subject_key, [])
            if topic not in lst:
                lst.append(topic)
                save_register(reg)
            return

def set_last_subject(roll, sk):
    reg = load_register()
    for s in reg["students"]:
        if s["roll"] == roll:
            if s.get("last_subject") != sk:
                s["last_subject"] = sk
                save_register(reg)
            return

# ---------------------------------------------------------------------------
# SAFE VIDEO LIBRARY — hand-verified, embeddable, kid-safe (plays INSIDE app).
# Kids never reach youtube.com, so they cannot wander to movies/other videos.
# Each item: (youtube_id, title, keywords_for_topic_match)
# ---------------------------------------------------------------------------
# Each item: (youtube_id, Roman-Urdu title, keywords_for_topic_match, lang)
# lang: "ur" = Urdu (allowed). All videos below verified to embed inside the app.
# Sources: Sparkles Online School (Urdu kids), + hand-picked Urdu channels.
SAFE_VIDEOS = {
    "math": [
        ("MADvSh9wzjA", "Kasoor (Fractions) — Hissa 1", "fraction kasoor fractions half quarter numbers adad", "ur"),
        ("UAZtHUtiRx0", "Kasoor (Fractions) — Hissa 2", "fraction kasoor fractions operations jama", "ur"),
        ("3HfKK6r97xI", "Kasron ki Jama", "fraction kasoor jama addition operations", "ur"),
        ("ESLe0NbeuUg", "3D Ashkaal (Shapes)", "shapes ashkaal geometry 3d cube square circle", "ur"),
        ("KzqDnckq2Ws", "Ginti 1 se 100 tak", "ginti numbers counting place value adad roman", "ur"),
    ],
    "science": [
        ("UNDuQO4g1BQ", "Roshni ki Energy (Light)", "roshni light energy saya shadow", "ur"),
        ("g7Vc91eSpmg", "Maddah — Solid (Matter)", "matter maddah solid liquid gas thos", "ur"),
        ("Ua2NEuLWS4o", "Nizam-e-Shamsi (Solar System)", "solar system nizam shamsi planets sun sooraj space", "ur"),
        ("zt7ZXhOyr6o", "Nizam-e-Shamsi — aur seekho", "solar system nizam shamsi planets space sitare", "ur"),
    ],
    "english": [
        ("ej24KVyEY4w", "English Grammar (Urdu mein)", "grammar noun verb tense sentence english punctuation", "ur"),
    ],
    "ai": [
        ("A4VKWkJ0CkU", "AI Kya Hai? (Urdu)", "ai artificial intelligence machine smart data chatbot", "ur"),
    ],
    "robotics": [
        ("A4VKWkJ0CkU", "Smart Machine / AI (Urdu)", "robot machine ai automatic smart sensor tech", "ur"),
    ],
}

# Only videos tagged with an allowed language are ever shown to students.
ALLOWED_VIDEO_LANGS = {"ur"}   # Urdu only — bachay aasani se samajh saken

def pick_videos(subject_key, topic):
    """Return curated Urdu videos for this subject, best topic match first.
    Videos not tagged as an allowed language (Urdu) are filtered out."""
    vids = [v for v in SAFE_VIDEOS.get(subject_key, [])
            if len(v) < 4 or v[3] in ALLOWED_VIDEO_LANGS]
    if not vids:
        return []
    tl = topic.lower()
    def match(v):
        return sum(1 for w in v[2].split() if w in tl)
    return sorted(vids, key=match, reverse=True)

def render_video_player(subject_key, topic):
    """Embed a curated video INSIDE the app (no YouTube browsing possible)."""
    import streamlit.components.v1 as components
    vids = pick_videos(subject_key, topic)
    if not vids:
        st.info("Is topic ke liye abhi video nahi hai.")
        return
    labels = [f"{i+1}. {v[1]}" for i, v in enumerate(vids)]
    choice = st.radio("Video chuno:", labels, key=f"vidpick_{subject_key}", label_visibility="collapsed")
    vid = vids[labels.index(choice)]
    # YouTube Player API + transparent click-shield: kids can only play/pause.
    # Every exit (YouTube logo, video title, "More videos" grid, fullscreen,
    # right-click menu, keyboard) is blocked so they cannot leave to YouTube.
    player_html = VIDEO_PLAYER_HTML.replace("__VID__", vid[0]).replace("__TITLE__", vid[1].replace('"', ""))
    components.html(player_html, height=390)

VIDEO_PLAYER_HTML = """
<div id="wrap" style="position:relative;width:100%;max-width:680px;margin:auto;border-radius:12px;overflow:hidden;background:#000">
  <div id="player"></div>
  <div id="shield" title="__TITLE__"
       style="position:absolute;inset:0;cursor:pointer;background:transparent;z-index:5"></div>
  <div id="hint"
       style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
              z-index:6;pointer-events:none;font-family:Segoe UI,sans-serif;color:#fff;
              font-size:3rem;text-shadow:0 2px 8px rgba(0,0,0,.7)">&#9654;</div>
</div>
<script>
(function(){
  var tag = document.createElement('script');
  tag.src = "https://www.youtube.com/iframe_api";
  document.head.appendChild(tag);
  var player, ready = false;
  var shield = document.getElementById('shield');
  var hint = document.getElementById('hint');
  window.onYouTubeIframeAPIReady = function(){
    player = new YT.Player('player', {
      width: '100%', height: '380', videoId: '__VID__',
      playerVars: {
        rel: 0, controls: 0, modestbranding: 1, disablekb: 1,
        fs: 0, iv_load_policy: 3, playsinline: 1, cc_load_policy: 0
      },
      events: {
        'onReady': function(){ ready = true; },
        'onStateChange': function(e){
          // 1 = playing -> hide hint; anything else -> show tap-to-play
          hint.innerHTML = (e.data === 1) ? '' : '&#9654;';
        }
      }
    });
  };
  shield.addEventListener('click', function(){
    if(!ready) return;
    var s = player.getPlayerState();
    if(s === 1){ player.pauseVideo(); } else { player.playVideo(); }
  });
  // block right-click (context menu has "Copy video URL" / "Watch on YouTube")
  document.getElementById('wrap').addEventListener('contextmenu', function(e){ e.preventDefault(); });
})();
</script>
"""

TTS_HTML = r"""
<div style="font-family:Segoe UI,sans-serif">
  <div style="display:flex;gap:8px;align-items:center">
    <button id="ttsPlay" style="flex:1;padding:10px;font-size:1.05rem;font-weight:700;color:#fff;
      background:#8e44ad;border:none;border-radius:12px;cursor:pointer">&#128266; Sunlo — sabaq suno!</button>
    <button id="ttsStop" style="padding:10px 16px;font-size:1.05rem;font-weight:700;color:#fff;
      background:#e74c3c;border:none;border-radius:12px;cursor:pointer">&#9209;&#65039; Roko</button>
  </div>
  <div style="margin-top:6px;display:flex;align-items:center;gap:6px">
    <span style="font-size:.8rem;color:#666">&#127908; Awaaz:</span>
    <select id="ttsVoice" style="flex:1;padding:4px;border-radius:8px;border:1px solid #ccc;font-size:.85rem"></select>
  </div>
  <div id="ttsStatus" style="font-size:0.78rem;color:#888;margin-top:4px"></div>
</div>
<script>
const raw = __TEXT__;
const clean = raw.replace(/[#*_`>|]/g, ' ').replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')  // noqa
                 .replace(/https?:\/\/\S+/g, ' ').replace(/\s+/g, ' ').trim();
let W = window;
try { if (window.parent && window.parent.speechSynthesis) W = window.parent; } catch (e) {}
const synth = W.speechSynthesis;
const playBtn = document.getElementById('ttsPlay');
const stopBtn = document.getElementById('ttsStop');
const sel = document.getElementById('ttsVoice');
const status = document.getElementById('ttsStatus');
const LS_KEY = 'ai4kids_tts_voice';

function score(v){
  const n = (v.name||'').toLowerCase(), l = (v.lang||'').toLowerCase();
  let s = 0;
  if (l === 'ur-pk' || l === 'ur') s += 200;
  else if (l.startsWith('ur')) s += 150;
  else if (l === 'hi-in' || l === 'hi') s += 80;
  else if (l.startsWith('hi')) s += 60;
  else if (l.startsWith('en')) s += 10;
  if (n.includes('female') || n.includes('uzma') || n.includes('google')) s += 5;
  return s;
}

function getAllVoices(){
  return synth.getVoices().sort((a,b) => score(b) - score(a));
}

function buildList(){
  const vs = getAllVoices();
  if (!vs.length) return false;
  sel.innerHTML = '';
  vs.forEach(v => {
    const o = document.createElement('option');
    const l = v.lang.toLowerCase();
    const tag = l.startsWith('ur') ? 'Urdu' : l.startsWith('hi') ? 'Hindi' : 'English';
    o.value = v.name;
    o.textContent = tag + ' — ' + v.name.replace('Microsoft ','').replace(/\s*-\s*Online.*$/,'').trim() + ' (' + v.lang + ')';
    sel.appendChild(o);
  });
  const saved = localStorage.getItem(LS_KEY);
  if (saved && vs.some(v => v.name === saved)) {
    sel.value = saved;
  } else {
    sel.value = vs[0].name;
  }
  const top = vs[0];
  const l = (top.lang||'').toLowerCase();
  if (l.startsWith('ur')) {
    status.textContent = 'Urdu awaaz mil gayi!';
  } else if (l.startsWith('hi')) {
    status.textContent = 'Hindi awaaz use hogi — Urdu se milti julti hai';
  } else {
    status.textContent = 'Urdu awaaz nahi mili — English awaaz use hogi';
  }
  return true;
}

function chosenVoice(){
  const vs = synth.getVoices();
  return vs.find(v => v.name === sel.value) || getAllVoices()[0] || null;
}

if (synth.getVoices().length > 0) {
  buildList();
} else {
  synth.onvoiceschanged = buildList;
  setTimeout(buildList, 1000);
}

sel.onchange = () => localStorage.setItem(LS_KEY, sel.value);

playBtn.onclick = () => {
  if (!clean) { status.textContent = 'Koi text nahi mila!'; return; }
  synth.cancel();
  const v = chosenVoice();
  const u = new W.SpeechSynthesisUtterance(clean);
  if (v) { u.voice = v; u.lang = v.lang; }
  u.rate = 0.88;
  u.pitch = 1.0;
  playBtn.innerHTML = '&#9654; Bol raha hai...';
  status.textContent = v ? ('Bol raha hai: ' + v.name) : 'Bol raha hai...';
  u.onend = () => { playBtn.innerHTML = '&#128266; Sunlo — sabaq suno!'; status.textContent = 'Mukammal!'; };
  u.onerror = (e) => { playBtn.innerHTML = '&#128266; Sunlo — sabaq suno!'; status.textContent = 'Error: ' + e.error; };
  synth.speak(u);
};

stopBtn.onclick = () => {
  synth.cancel();
  playBtn.innerHTML = '&#128266; Sunlo — sabaq suno!';
  status.textContent = '';
};
</script>
"""

def tts_button(text):
    """Free browser text-to-speech — reads lesson aloud for kids."""
    import streamlit.components.v1 as components
    components.html(TTS_HTML.replace("__TEXT__", json.dumps(text)), height=120)

def tts_urdu_install_tip():
    """Show a one-time tip to install Urdu voice on Windows."""
    with st.expander("🔊 Urdu awaaz kaise install karein? (Windows)"):
        st.markdown("""
**Urdu (Pakistan) awaaz free mein install karein:**

1. **Windows key** dabao → **Settings** khulay
2. **Time & Language** → **Speech** par click karo
3. **"Add voices"** button dabao
4. Search mein **"Urdu"** likho
5. **Urdu (Pakistan)** chunein → **Add** karo
6. Download hone ke baad browser **refresh** karo
7. Awaaz dropdown mein **"Urdu — Microsoft Urdu Online"** dikhe ga

Urdu nahi mila? **Hindi — Google हिन्दी** chunein — Roman Urdu ke liye sab se achi awaaz hai!
        """)


# =====================================================================
#  MAIN DOOR
# =====================================================================
if st.session_state.mode == "door":
    st.markdown("---")
    if os.path.exists(_app("school_door.jpeg")):
        c1, c2, c3 = st.columns([2, 1, 2])
        c2.image(_app("school_door.jpeg"), width=150)
    st.markdown('<h2 style="text-align:center">🚪 School ka darwaza — andar aayein!</h2>', unsafe_allow_html=True)

    # KB MODE ka notice — sirf jab API key set na ho (demo school)
    if not AI_ENABLED:
        st.markdown(
            '<div style="text-align:center;padding:14px 16px;background:#eaf4fb;'
            'border:2px solid #3498db;border-radius:14px;margin:10px 0">'
            '<b>📚 Yeh AI4Kids ka DEMO school hai</b><br>'
            '<span style="font-size:0.95em">150 tayyar sabaq, 150 quiz, awaaz aur tasveerein — '
            'sab kaam kar rahe hain. Naye AI sabaq is demo mein band hain.<br>'
            'Poora school apne bachay ke liye chahiye? '
            '<b>WhatsApp: 0301-5144308</b></span>'
            '</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div style="text-align:center;padding:20px;border:2px solid #2ecc71;border-radius:12px;background:#eafaf1"><h3>🧑‍🏫 Teacher / Admin</h3><p>Daakhla, record, agents</p></div>', unsafe_allow_html=True)
        # --- Admin office ka apna alag password (cloud par) ---
        if not ADMIN_PASSWORD or st.session_state.get("admin_ok"):
            if st.button("🔑 Admin mein jao", width='stretch'):
                go(mode="admin"); st.rerun()
        else:
            _apw = st.text_input("Admin password", type="password",
                                 key="admin_pw", label_visibility="collapsed",
                                 placeholder="Admin ka password")
            if st.button("🔑 Admin mein jao", width='stretch'):
                if _apw == ADMIN_PASSWORD:
                    st.session_state.admin_ok = True
                    go(mode="admin"); st.rerun()
                else:
                    st.error("❌ Admin password ghalat hai.")
    with c2:
        st.markdown('<div style="text-align:center;padding:20px;border:2px solid #9b59b6;border-radius:12px;background:#f5eef8"><h3>🎒 Student</h3><p>Class mein jao — seekho aur khelo!</p></div>', unsafe_allow_html=True)
        if st.button("📚 Class mein jao", width='stretch'):
            reset_student_session()      # always start at the name-picker
            go(mode="student"); st.rerun()

    if os.path.exists(LESSON_BANK_PATH):
        st.markdown(
            '<div style="text-align:center;padding:14px;border:2px solid #f39c12;'
            'border-radius:12px;background:#fffbea;margin-top:10px">'
            '<h3>📚 Lesson Bank — سبق خزانہ</h3>'
            '<p>SNC Curriculum (Class 1-5) + saved lessons + curated videos</p>'
            '</div>', unsafe_allow_html=True)
        c_lb, c_cur = st.columns(2)
        with c_lb:
            if st.button("📚 Lesson Bank & Curriculum kholo", width='stretch', key="mdoor_lb"):
                st.session_state.view_lessonbank = not st.session_state.get("view_lessonbank", False)
                st.rerun()
        with c_cur:
            if os.path.exists(CURRICULUM_PATH):
                if st.button("📖 Curriculum — Class 1-5 (FBISE/SNC)", width='stretch', key="mdoor_cur"):
                    st.session_state.view_curriculum = not st.session_state.get("view_curriculum", False)
                    st.rerun()
        render_html_viewers()
    elif os.path.exists(CURRICULUM_PATH):
        if st.button("📖 Curriculum dekho — Class 1-5 (FBISE/SNC)", width='stretch', key="mdoor_cur2"):
            st.session_state.view_curriculum = not st.session_state.get("view_curriculum", False)
            st.rerun()
        render_html_viewers()


# =====================================================================
#  STUDENT MODE
# =====================================================================
elif st.session_state.mode == "student":
    student = get_student_by_roll(st.session_state.stu_roll)

    nav1, nav2 = st.columns(2)
    with nav1:
        if st.button("🏠 Ghar / Main Door", width='stretch'):
            reset_student_session()
            go(mode="door"); st.rerun()
    with nav2:
        if student is not None and st.session_state.stu_screen not in ("assembly", "hallway"):
            if st.button("🏫 Hallway / Classes", width='stretch'):
                go(screen="hallway"); st.session_state.lesson_result = None
                st.session_state.quiz_result = None; st.rerun()

    # --- LOGIN ---
    if student is None:
        st.markdown("---")
        st.markdown('<h2 style="text-align:center">🎒 Apna naam chunein!</h2>', unsafe_allow_html=True)
        if not register["students"]:
            st.warning("Koi student nahi hai. Admin mein daakhla karein!"); st.stop()
        for s in register["students"]:
            if st.button(f"**{s['name']}** — Roll {s['roll']}, Grade {s['grade']}, {s['section']}  |  ⭐ {s['stars']}", key=f"stu_{s['roll']}_{s['name']}", width='stretch'):
                go(roll=s["roll"]); st.session_state.assembly_done = False
                st.session_state.ui_mode = get_mode(s["grade"])
                reg2 = load_register()
                for s2 in reg2["students"]:
                    if s2["roll"] == s["roll"]: mark_attendance(reg2, s2)
                st.rerun()
        st.stop()

    # --- LOGGED IN ---
    student = get_student_by_roll(st.session_state.stu_roll)
    grade = student["grade"]
    st.session_state.ui_mode = get_mode(grade)  # keep tier in sync with grade
    ui_mode = st.session_state.ui_mode
    tt, day_name = get_today_timetable()
    screen = st.session_state.stu_screen
    scroll_to_top()

    # ========================
    #  ASSEMBLY
    # ========================
    if screen == "assembly" and not st.session_state.assembly_done:
        streak = get_streak(student)
        s_emoji, s_msg = streak_badge(streak)
        st.markdown(
            f'<div style="text-align:center;padding:20px;background:linear-gradient(135deg,#fef9e7,#eafaf1);'
            f'border-radius:16px;border:2px solid #f39c12">'
            f'<h1>🔔 TRING TRING! 🔔</h1>'
            f'<h2>Assalamu Alaikum, {student["name"]}!</h2>'
            f'<p style="font-size:1.1em">Roll {student["roll"]} | Grade {grade} | {student["section"]} Section</p>'
            f'<p>⭐ {student["stars"]} stars | 📅 Hazri: {len(student["attendance"])} din</p>'
            f'<hr><p style="font-size:1.2em">✅ Aaj ki hazri lag gayi! +1 star</p>'
            f'<p style="font-size:1.5em">{s_emoji} {s_msg}</p>'
            f'{"<p style=font-size:2em>🔥🔥🔥 STREAK ON FIRE! 🔥🔥🔥</p>" if streak >= 5 else ""}'
            f'<p>📅 Aaj <b>{day_name}</b> hai</p>'
            f'</div>', unsafe_allow_html=True)

        # ---- SIMPLE ASSEMBLY (Grade 1-2): bell -> hazri -> aaj ka lafz -> one big button ----
        if ui_mode == "SIMPLE":
            _sw, _sw_emoji, _sw_mean = get_word_of_day_simple()
            st.markdown(
                f'<div style="text-align:center;padding:18px 14px;background:#f5eef8;'
                f'border-radius:22px;border:3px solid #9b59b6;margin-top:14px">'
                f'<p style="font-size:17px;color:#8e44ad;margin:0 0 4px 0">Aaj ka lafz</p>'
                f'<div style="font-size:66px;line-height:1.1">{_sw_emoji}</div>'
                f'<div style="font-size:36px;font-weight:800;color:#6c3483;margin:4px 0">{_sw}</div>'
                f'<div style="font-size:21px;color:#2c3e50">{_sw_mean}</div>'
                f'</div>', unsafe_allow_html=True)
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            if st.button("🚪 Class Mein Jao", width='stretch', type="primary",
                         key=f"simple_assembly_go_{student['roll']}"):
                st.session_state.assembly_done = True
                go(screen="hallway")
                st.rerun()
            st.stop()

        st.markdown("---")

        # ---- HOMEWORK CHECK ----
        pending_hw = get_pending_homework(student["roll"])
        if pending_hw:
            hw = pending_hw[0]
            age = (datetime.date.today() - datetime.date.fromisoformat(hw["date"])).days
            st.markdown(
                f'<div style="padding:16px;background:#fff3cd;border-radius:14px;'
                f'border:3px solid #f39c12;margin-bottom:12px">'
                f'<h3>📓 Kal ka Homework — Check karo!</h3>'
                f'<p><b>{hw["subject"]}</b> — {hw["topic"]}</p>'
                f'<p style="font-size:1.1em;background:#fff;padding:10px;border-radius:8px">'
                f'📝 {hw["task"]}</p>'
                f'</div>', unsafe_allow_html=True)
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("✅ Haan! Kiya tha!", width='stretch', type="primary"):
                    mark_hw_done(student["roll"], hw["date"])
                    reg_hw = load_register()
                    for s_hw in reg_hw["students"]:
                        if s_hw["roll"] == student["roll"]:
                            s_hw["stars"] += 3
                            save_register(reg_hw)
                            break
                    st.success("Wah! Zimmedaar student! +3 stars! 🌟")
                    st.rerun()
            with c_no:
                if st.button("😔 Nahi ho saka", width='stretch'):
                    mark_hw_done(student["roll"], hw["date"])
                    st.info("Koi baat nahi — aaj zaroor karna! 💪")
                    st.rerun()

        st.markdown('<h3 style="text-align:center">📋 Aaj ka timetable</h3>', unsafe_allow_html=True)

        for i, subj_key in enumerate(tt):
            subj = SUBJECTS[subj_key]
            st.markdown(
                f'<div style="display:flex;align-items:center;padding:8px 12px;margin:4px 0;'
                f'border-left:4px solid {subj["color"]};background:{subj["bg"]};border-radius:0 8px 8px 0">'
                f'<span style="min-width:70px;font-weight:500">Period {i+1}</span>'
                f'<span style="min-width:50px;color:#888">{PERIOD_TIMES[i]}</span>'
                f'<span>{subj["emoji"]} <b>{subj["name"]}</b> — {subj["teacher"]}</span>'
                f'</div>', unsafe_allow_html=True)

        # WORD OF THE DAY
        eng, urdu, meaning = get_word_of_day()
        st.markdown("---")
        st.markdown(
            f'<div style="text-align:center;padding:16px;background:#f5eef8;'
            f'border-radius:12px;border:2px solid #9b59b6">'
            f'<p style="font-size:0.9em;color:#8e44ad;margin:0">📖 Aaj ka lafz / Word of the Day</p>'
            f'<h2 style="margin:4px 0;color:#6c3483">{eng}</h2>'
            f'<p style="font-size:1.3em;font-family:serif;direction:rtl;margin:4px 0">{urdu}</p>'
            f'<p style="margin:4px 0">{meaning}</p>'
            f'</div>', unsafe_allow_html=True)

        st.markdown("---")

        # JUMA TEST ANNOUNCEMENT
        if is_juma_today():
            already_done = has_done_juma_test(student["roll"])
            if already_done:
                jc = load_juma_cache()
                wk = get_this_week_monday().isoformat()
                result = jc.get(str(student["roll"]), {}).get(wk, {})
                sc, tot = result.get("score", 0), result.get("total", 10)
                st.markdown(
                    f'<div style="text-align:center;padding:14px;background:#eafaf1;'
                    f'border-radius:12px;border:2px solid #27ae60;margin-bottom:8px">'
                    f'<h3>✅ Juma Test ho gaya! {sc}/{tot} — Shabash!</h3>'
                    f'<p>Agli baar Juma ko milenge!</p></div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="text-align:center;padding:16px;background:#fff3cd;'
                    f'border-radius:12px;border:3px solid #f39c12;margin-bottom:8px">'
                    f'<h2>📋 Juma Test! Hafta bhar ka imtehaan!</h2>'
                    f'<p>Aaj Juma hai — is hafta ke tamam subjects ka test hoga!</p>'
                    f'<p>10 sawaal • 5 subjects • Sirf {student["name"]} ke liye</p>'
                    f'</div>', unsafe_allow_html=True)
                if st.button("📋 Juma Test shuru karo!", width='stretch', type="primary"):
                    qs = build_juma_questions(student, grade)
                    st.session_state.juma_questions = qs
                    st.session_state.juma_current = 0
                    st.session_state.juma_answers = []
                    st.session_state.juma_done = False
                    st.session_state.assembly_done = True
                    go(screen="juma_test")
                    st.rerun()

        if st.button("🏫 Chalo class mein chalein!", width='stretch', type="primary"):
            st.session_state.assembly_done = True
            go(screen="hallway")
            st.rerun()

    # ========================
    #  HALLWAY (pick classroom)
    # ========================
    elif screen == "hallway":
        # Student bar
        streak = get_streak(student)
        s_emoji, s_msg = streak_badge(streak)
        st.markdown(
            f'<div style="text-align:center;padding:8px;background:#eafaf1;border-radius:8px;border:1px solid #27ae60">'
            f'<b>{student["name"]}</b> | Grade {grade} | ⭐ {student["stars"]} | {s_emoji} {streak} din streak | 📅 {day_name}'
            f'</div>', unsafe_allow_html=True)

        st.markdown('<h2 style="text-align:center">🏫 School hallway — kis class mein jaoge?</h2>', unsafe_allow_html=True)

        # Show timetable hint
        st.caption(f"📋 Aaj ka schedule: {' → '.join([SUBJECTS[s]['emoji'] for s in tt])}")

        last_sk = student.get("last_subject")
        if last_sk in SUBJECTS:
            _ls = SUBJECTS[last_sk]
            if st.button(f"▶️ Jahan chhora tha wahin se — {_ls['emoji']} {_ls['name']}", width='stretch', type="primary"):
                go(screen="classroom", subject=last_sk)
                st.session_state.lesson_result = None; st.session_state.quiz_result = None
                st.rerun()

        # Classroom doors — SIMPLE (Grade 1-2) gets only 3 doors
        if ui_mode == "SIMPLE":
            subj_keys = ["ai", "english", "math"]
            all_cols = list(st.columns(3))
        else:
            subj_keys = ["ai", "robotics", "english", "math", "science"]
            cols_row1 = st.columns(3)
            cols_row2 = st.columns(2)
            all_cols = list(cols_row1) + list(cols_row2)

        for i, sk in enumerate(subj_keys):
            subj = SUBJECTS[sk]
            col = all_cols[i]
            with col:
                period_num = tt.index(sk) + 1 if sk in tt else 0
                st.markdown(
                    f'<div style="text-align:center;padding:16px;border:2px solid {subj["border"]};'
                    f'border-radius:12px;background:{subj["bg"]};min-height:140px">'
                    f'<h3>{subj["emoji"]} {subj["name"]}</h3>'
                    f'<p>{subj["teacher"]}</p>'
                    f'<p style="font-size:0.8em;color:#888">Period {period_num} | {PERIOD_TIMES[period_num-1]}</p>'
                    f'</div>', unsafe_allow_html=True)
                if st.button(f"🚪 {subj['name']} mein jao", key=f"door_{sk}", width='stretch'):
                    go(screen="classroom", subject=sk)
                    set_last_subject(student["roll"], sk)
                    st.session_state.lesson_result = None
                    st.session_state.quiz_result = None
                    st.rerun()

        st.markdown("---")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("💬 Teacher se baat", width='stretch'):
                go(screen="chat"); st.rerun()
        with c2:
            if st.button("🏆 Report card", width='stretch'):
                go(screen="report"); st.rerun()
        with c3:
            if st.button("🔔 Chhuti!", width='stretch'):
                go(screen="chhuti"); st.rerun()
        with c4:
            if st.button("🚪 Logout", width='stretch'):
                reset_student_session()
                go(mode="door"); st.rerun()

        # ---- LEADERBOARD ---- (hidden in SIMPLE mode for Grade 1-2)
        if ui_mode == "SIMPLE":
            st.stop()

        st.markdown("---")
        st.markdown('<h3 style="text-align:center">🏆 Leaderboard — Top Students</h3>', unsafe_allow_html=True)

        all_students = sorted(load_register()["students"], key=lambda x: x["stars"], reverse=True)
        medals = ["🥇", "🥈", "🥉"]

        # Overall top 3
        for i, s in enumerate(all_students[:3]):
            streak_s = get_streak(s)
            s_em, _ = streak_badge(streak_s)
            is_me = " ← YEH TUM HO!" if s["roll"] == student["roll"] else ""
            bg = "#fffbea" if i == 0 else "#f9f9f9"
            st.markdown(
                f'<div style="display:flex;align-items:center;padding:10px 14px;margin:4px 0;'
                f'background:{bg};border-radius:8px;border:1px solid #eee">'
                f'<span style="font-size:1.5em;min-width:40px">{medals[i]}</span>'
                f'<span style="flex:1"><b>{s["name"]}</b> — Grade {s["grade"]}, {s["section"]}</span>'
                f'<span style="min-width:80px;text-align:right">⭐ {s["stars"]}</span>'
                f'<span style="min-width:40px;text-align:right">{s_em}</span>'
                f'<span style="color:#e74c3c;font-weight:bold">{is_me}</span>'
                f'</div>', unsafe_allow_html=True)

        # Section leaderboard
        my_section = student["section"]
        section_students = [s for s in all_students if s["section"] == my_section]
        if len(section_students) > 1:
            st.markdown(f"**{my_section} Section ranking:**")
            for i, s in enumerate(section_students[:5]):
                streak_s = get_streak(s)
                s_em, _ = streak_badge(streak_s)
                marker = " ⬅️" if s["roll"] == student["roll"] else ""
                st.caption(f"{i+1}. {s['name']} — ⭐ {s['stars']} {s_em}{marker}")

        # Streak champions
        streaks = [(s["name"], get_streak(s), s["roll"]) for s in all_students if get_streak(s) >= 2]
        if streaks:
            streaks.sort(key=lambda x: x[1], reverse=True)
            st.markdown("**🔥 Streak champions:**")
            for name, sk, roll in streaks[:3]:
                s_em, s_msg = streak_badge(sk)
                marker = " ⬅️" if roll == student["roll"] else ""
                st.caption(f"{s_em} {name} — {sk} din lagataar!{marker}")

    # ========================
    #  CLASSROOM (subject-specific)
    # ========================
    elif screen == "classroom":
        sk = st.session_state.stu_subject
        subj = SUBJECTS[sk]
        topics = get_topics(sk, grade)

        if st.button("⬅️ Wapas hallway"):
            go(screen="hallway"); st.session_state.lesson_result = None; st.rerun()

        done_list = get_done_topics(student, sk)
        if topics:
            _dc = sum(1 for _t, _d in topics if _t in done_list)
            st.progress(_dc / len(topics), text=f"✅ {_dc}/{len(topics)} topics mukammal (quiz pass karke ✅ lo)")
        _curr = get_curriculum_topics(sk, grade)
        if _curr:
            with st.expander(f"📚 SNC/FBISE Curriculum — Grade {min(max(grade,1),5)} {CURR_SUBJ_MAP.get(sk,'')} ({len(_curr)} topics)"):
                for _ct in _curr:
                    st.markdown(f"- {_ct}")

        # Classroom header (decorated wall)
        ROOM_DECOR = {
            "ai": {
                "wall_items": "🤖 🧠 💻 📱 🎮 🖥️ 🤖 🧠 💻 📱",
                "blackboard": "Chalo AI seekhte hain!",
                "desk_items": "💻 Laptop | 🖱️ Mouse | 📒 Notebook",
                "poster1": "🤖 Robot Gallery",
                "poster2": "🧠 Brain vs Computer",
                "floor": "Circuit board pattern tiles",
                "window": "🌆 Islamabad skyline",
            },
            "robotics": {
                "wall_items": "⚙️ 🔧 🔩 🦾 🛠️ 🏗️ ⚙️ 🔧 🔩 🦾",
                "blackboard": "Aaj machine banayenge!",
                "desk_items": "🔧 Tools | ⚙️ Gears | 🔌 Wires",
                "poster1": "🦾 Robotic Arms",
                "poster2": "🚁 Drone Models",
                "floor": "Workshop rubber mat",
                "window": "🏭 Factory view",
            },
            "english": {
                "wall_items": "📚 ✏️ 📖 🔤 📝 🎭 📚 ✏️ 📖 🔤",
                "blackboard": "Let's read and write!",
                "desk_items": "📖 Story Book | ✏️ Pencil | 📓 Diary",
                "poster1": "🔤 Alphabet Chart",
                "poster2": "📚 Word Wall",
                "floor": "Colorful carpet with letters",
                "window": "🌳 Garden view",
            },
            "math": {
                "wall_items": "🔢 📐 📏 ➕ ✖️ 🔺 🔢 📐 📏 ➕",
                "blackboard": "Hisaab mein mazaa hai!",
                "desk_items": "📐 Ruler | 🧮 Abacus | ✏️ Pencil",
                "poster1": "✖️ Times Tables",
                "poster2": "🔺 Shapes Chart",
                "floor": "Number line on floor",
                "window": "🏪 Bazaar view (for math problems!)",
            },
            "science": {
                "wall_items": "🔬 🧪 🌱 🦎 🌍 ☀️ 🔬 🧪 🌱 🦎",
                "blackboard": "Aaj experiment karenge!",
                "desk_items": "🔬 Microscope | 🧪 Test Tube | 📋 Lab Sheet",
                "poster1": "🌍 Solar System",
                "poster2": "🌱 Plant Life Cycle",
                "floor": "Lab tiles (white + grey)",
                "window": "🏔️ Margalla Hills view",
            },
        }
        decor = ROOM_DECOR.get(sk, ROOM_DECOR["ai"])

        period_num = tt.index(sk) + 1 if sk in tt else 1
        st.markdown(
            f'<div style="padding:0;margin-bottom:16px">'

            # CEILING: lights, fan, clock, flag
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:6px 20px;background:linear-gradient(#dfe6e9,#f5f6fa);'
            f'border:2px solid {subj["border"]};border-radius:16px 16px 0 0;font-size:1.2em">'
            f'<span>🇵🇰</span><span>💡</span>'
            f'<span style="font-size:1.6em">🌀</span>'
            f'<span>💡</span>'
            f'<span style="font-size:0.7em;background:#fff;padding:2px 8px;border-radius:10px;'
            f'border:1px solid #999">🕐 {PERIOD_TIMES[period_num-1]} | Period {period_num}</span>'
            f'</div>'

            # DOOR + wall items
            f'<div style="display:flex;align-items:center;background:{subj["bg"]};'
            f'border-left:2px solid {subj["border"]};border-right:2px solid {subj["border"]}">'
            f'<div style="padding:8px 10px;font-size:1.8em" title="Darwaza">🚪</div>'
            f'<div style="flex:1;text-align:center;padding:8px;letter-spacing:6px;font-size:1.2em">'
            f'{decor["wall_items"]}</div>'
            f'<div style="padding:8px 10px;font-size:1.5em" title="Khidki">🪟</div>'
            f'</div>'

            # BLACKBOARD with teacher standing beside
            f'<div style="display:flex;align-items:stretch;gap:8px;margin:0;padding:0 14px;'
            f'background:{subj["bg"]};border-left:2px solid {subj["border"]};border-right:2px solid {subj["border"]}">'
            f'<div style="display:flex;flex-direction:column;justify-content:flex-end;align-items:center;font-size:2.4em;padding-bottom:4px" '
            f'title="{subj["teacher"]}">🧑‍🏫</div>'
            f'<div style="flex:1;text-align:center;padding:18px;'
            f'background:#2c3e50;border-radius:8px;border:6px solid #8B4513;'
            f'box-shadow:inset 0 0 20px rgba(0,0,0,0.35)">'
            f'<p style="color:#fff;font-size:0.8em;margin:0">📋 {subj["teacher"]} ka Board</p>'
            f'<h2 style="color:#e8e8e8;font-family:serif;margin:4px 0">{decor["blackboard"]}</h2>'
            f'<p style="color:#aaa;font-size:0.75em;margin:0">{subj["emoji"]} {subj["name"]} — Grade {grade}</p>'
            f'<div style="text-align:left;margin-top:6px"><span style="background:#fff;padding:1px 6px;'
            f'border-radius:3px;font-size:0.7em">🖍️ chalk</span> '
            f'<span style="background:#c0392b;color:#fff;padding:1px 6px;border-radius:3px;font-size:0.7em">🧽 duster</span></div>'
            f'</div>'
            f'</div>'

            # POSTERS + NOTICE BOARD
            f'<div style="display:flex;justify-content:space-between;gap:8px;margin:0;padding:8px 14px;'
            f'background:{subj["bg"]};border-left:2px solid {subj["border"]};border-right:2px solid {subj["border"]}">'
            f'<div style="padding:6px 12px;background:#fffbea;border:2px dashed {subj["color"]};'
            f'border-radius:8px;font-size:0.8em">{decor["poster1"]}</div>'
            f'<div style="padding:6px 12px;background:#d5f5e3;border:2px solid #27ae60;'
            f'border-radius:8px;font-size:0.8em">📌 Notice: Aaj {day_name} hai!</div>'
            f'<div style="padding:6px 12px;background:#fffbea;border:2px dashed {subj["color"]};'
            f'border-radius:8px;font-size:0.8em">{decor["poster2"]}</div>'
            f'</div>'

            # CLASSMATE DESK ROWS (rows of desks, student's own seat highlighted)
            f'<div style="text-align:center;padding:6px 14px;background:{subj["bg"]};'
            f'border-left:2px solid {subj["border"]};border-right:2px solid {subj["border"]};'
            f'font-size:1.3em;letter-spacing:12px">🪑 🪑 🪑 🪑</div>'
            f'<div style="text-align:center;padding:2px 14px 6px;background:{subj["bg"]};'
            f'border-left:2px solid {subj["border"]};border-right:2px solid {subj["border"]};'
            f'font-size:1.3em;letter-spacing:12px">🪑 <span style="background:#fff3cd;'
            f'border:2px solid #f39c12;border-radius:6px;padding:0 6px">🎒</span> 🪑 🪑</div>'

            # STUDENT'S DESK (front)
            f'<div style="display:flex;justify-content:space-between;align-items:center;'
            f'padding:10px 16px;background:linear-gradient(#deb887,#c8a165);'
            f'border:2px solid {subj["border"]};border-top:3px solid #8B4513;'
            f'border-radius:0 0 16px 16px">'
            f'<div>🪑 <b>{student["name"]}</b> ki seat | ⭐ {student["stars"]}</div>'
            f'<div style="font-size:0.85em;color:#4a3520">{decor["desk_items"]}</div>'
            f'</div>'

            f'</div>', unsafe_allow_html=True)

        # Window view (small caption)
        st.caption(f"🪟 Khidki se nazara: {decor['window']} | Floor: {decor['floor']}")

        # Lesson or Quiz tabs
        ghalti_n = get_ghalti_count(student["roll"])
        ghalti_tab_label = f"📒 Ghalti Copy ({ghalti_n})" if ghalti_n > 0 else "📒 Ghalti Copy"
        tab1, tab2, tab3 = st.tabs([f"📖 {subj['teacher']} ka sabaq", "📝 Examiner Sahib ka quiz", ghalti_tab_label])

        with tab1:
            if st.session_state.lesson_result is None:
                # ---- TOPIC MAP with ✅ / 🔓 / 🔒 ----
                done_set = set(done_list)
                ghalti_topics = set(
                    e["topic"] for e in load_ghalti().get(str(student["roll"]), [])
                    if e["subject"] == sk
                )

                st.markdown(
                    f'<div style="padding:10px 14px;background:#f5f5f5;border-radius:10px;'
                    f'border-left:4px solid {subj["color"]};margin-bottom:10px">'
                    f'<b>Sabaq ka safar</b> — {len(done_set)}/{len(topics)} topics complete'
                    f'{"  🎉 SUBJECT MUKAMMAL!" if len(done_set) == len(topics) else ""}'
                    f'</div>', unsafe_allow_html=True)

                for idx, (title, desc) in enumerate(topics):
                    is_done     = title in done_set
                    is_locked   = idx > 0 and topics[idx-1][0] not in done_set
                    has_ghalti  = title in ghalti_topics
                    in_progress = not is_done and not is_locked

                    # Status visuals
                    if is_done:
                        icon, border, bg, btn_type = "✅", "#27ae60", "#eafaf1", "secondary"
                        status_txt = "Mukammal!"
                    elif is_locked:
                        icon, border, bg, btn_type = "🔒", "#bdc3c7", "#f8f9fa", "secondary"
                        status_txt = f"Pehle '{topics[idx-1][0]}' mukammal karo"
                    elif has_ghalti:
                        icon, border, bg, btn_type = "📒", "#f39c12", "#fef9e7", "primary"
                        status_txt = "Ghalti Copy mein hai — dobara karo!"
                    else:
                        icon, border, bg, btn_type = "🔓", subj["color"], subj["bg"], "primary"
                        status_txt = "Tayyar hai — shuru karo!"

                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(
                            f'<div style="padding:10px 14px;border:2px solid {border};'
                            f'border-radius:10px;background:{bg};margin:4px 0">'
                            f'<span style="font-size:1.2em">{icon}</span> '
                            f'<b>{title}</b><br>'
                            f'<span style="font-size:0.82em;color:#666">{desc}</span><br>'
                            f'<span style="font-size:0.78em;color:{border}">{status_txt}</span>'
                            f'</div>', unsafe_allow_html=True)
                    with col2:
                        if not is_locked:
                            btn_label = "✅ Dobara" if is_done else ("📒 Review" if has_ghalti else "▶️ Shuru")
                            if st.button(btn_label, key=f"lt_{sk}_{idx}",
                                         width='stretch', type=btn_type):
                                kb_lesson, _ = load_kb_topic(sk, grade, title)
                                st.session_state.show_simple_quiz = False
                                st.session_state.simple_audio_topic = None
                                st.session_state.simple_quiz_idx = 0
                                if kb_lesson:
                                    st.session_state.lesson_result = {"topic":title,"content":kb_lesson,"teacher":subj["teacher"]+" (KB)"}
                                    st.session_state.lessons_today += 1
                                    st.rerun()
                                else:
                                    cached_l = get_cached_lesson(sk, title, grade)
                                    if cached_l:
                                        st.session_state.lesson_result = {"topic":title,"content":cached_l,"teacher":subj["teacher"]+" (saved)"}
                                        st.session_state.lessons_today += 1
                                    else:
                                        with st.spinner(f"{subj['teacher']} sabaq tayyar kar rahe hain..."):
                                            req = f"Grade {grade} {subj['name']} lesson: {desc}. Roman Urdu."
                                            ans = run_agent(subj["prompt"], req + student_context(student), 3000)
                                            save_record(subj["folder"], req, ans, student)
                                            save_lesson_to_cache(sk, title, grade, ans)
                                            st.session_state.lesson_result = {"topic":title,"content":ans,"teacher":subj["teacher"]}
                                            st.session_state.lessons_today += 1
                                    st.rerun()
                        else:
                            st.button("🔒", key=f"lt_{sk}_{idx}", width='stretch', disabled=True)
            else:
                r = st.session_state.lesson_result

                # ---- SIMPLE MODE lesson (Grade 1-2): big emoji, no checkpoints/FITB ----
                if ui_mode == "SIMPLE":
                    if st.button("⬅️ Wapas", width='stretch',
                                 key=f"simple_back_{sk}"):
                        go(screen="hallway")
                        st.session_state.lesson_result = None
                        st.session_state.show_simple_quiz = False
                        st.session_state.simple_audio_topic = None
                        st.rerun()
                    st.markdown(
                        f'<div style="text-align:center;font-size:22px;font-weight:700;'
                        f'color:{subj.get("color", "#f39c12")}">{subj["emoji"]} {r["topic"]}</div>',
                        unsafe_allow_html=True)

                    if not st.session_state.get("show_simple_quiz"):
                        render_topic_interactive(sk, grade, r["topic"])
                        _res = render_simple_lesson(sk, grade, r["topic"], student, subj)
                        if _res == "quiz":
                            st.session_state.show_simple_quiz = True
                            st.session_state.simple_quiz_idx = 0
                            st.rerun()
                    else:
                        if "render_simple_quiz" in globals():
                            render_simple_quiz(sk, grade, r["topic"], student, subj)
                        else:
                            st.info("🎉 Sabaq mukammal! (Quiz Step 4 mein aayega)")
                            if st.button("⬅️ Wapas hallway", width='stretch',
                                         key=f"simple_q_back_{sk}"):
                                go(screen="hallway")
                                st.session_state.lesson_result = None
                                st.session_state.show_simple_quiz = False
                                st.rerun()
                    st.stop()

                st.success(f"📖 {r['topic']} — {r['teacher']}")

                # Hand-drawn teaching picture (fractions/circuits/shapes...) — free, no API
                _vis_std = get_topic_visual(sk, grade, r["topic"])
                if _vis_std:
                    st.markdown(_vis_std, unsafe_allow_html=True)
                render_money_photos(r["topic"])

                # Class 5 HTML micro-lesson (if wired in KB)
                render_topic_interactive(sk, grade, r["topic"])

                # Action buttons ABOVE lesson content (always visible)
                c1, c2, c3 = st.columns(3)
                with c1:
                    _vlabel = "🎬 Video band karo" if st.session_state.show_video else "🎬 Video dekho"
                    if st.button(_vlabel, width='stretch'):
                        st.session_state.show_video = not st.session_state.show_video
                        st.rerun()
                with c2:
                    if st.button("📝 Quiz lo!", width='stretch'):
                        t = r["topic"]
                        # Fix 3: always use KB → quiz_cache → MCQ system (never old EXAMINER)
                        _, kb_q = load_kb_topic(sk, grade, t)
                        if kb_q and "questions" in kb_q and len(kb_q["questions"]) > 0:
                            st.session_state.mcq_questions = kb_q["questions"]
                            st.session_state.mcq_topic = kb_q.get("title", t)
                            st.session_state.mcq_current = 0
                            st.session_state.mcq_answers = []
                            st.session_state.mcq_done = False
                            st.rerun()
                        else:
                            cached_q = get_cached_quiz(sk, t, grade)
                            if cached_q and "questions" in cached_q:
                                st.session_state.mcq_questions = cached_q["questions"]
                                st.session_state.mcq_topic = cached_q.get("title", t)
                                st.session_state.mcq_current = 0
                                st.session_state.mcq_answers = []
                                st.session_state.mcq_done = False
                                st.rerun()
                            else:
                                diff = get_student_difficulty(student, sk, t)
                                with st.spinner("Examiner Sahib quiz tayyar kar rahe hain..."):
                                    req = f"Grade {grade} {subj['name']} quiz about '{t}'. DIFFICULTY: {diff.upper()}. 5 MCQ. ROMAN URDU ONLY."
                                    ans = run_agent(MCQ_EXAMINER_PROMPT, req + student_context(student), 3000)
                                    try:
                                        qd = parse_json(ans)
                                        if "questions" in qd and len(qd["questions"]) > 0:
                                            save_quiz_to_cache(sk, t, grade, qd)
                                            save_record("quizzes", req, ans, student)
                                            st.session_state.mcq_questions = qd["questions"]
                                            st.session_state.mcq_topic = qd.get("title", t)
                                            st.session_state.mcq_current = 0
                                            st.session_state.mcq_answers = []
                                            st.session_state.mcq_done = False
                                    except:
                                        st.error("Quiz nahi ban saka — dobaara try karein!")
                                st.rerun()
                with c3:
                    if st.button("📖 Doosra topic", width='stretch'):
                        st.session_state.lesson_result = None; st.session_state.show_video = False; st.session_state.urdu_summary = None; st.rerun()

                if st.session_state.show_video:
                    st.markdown("🎬 **Topic video (app ke andar):**")
                    render_video_player(sk, r["topic"])
                st.markdown("---")
                if st.button("📝 Roman Urdu mein summary banao", width='stretch', key="urdu_sum_btn"):
                    with st.spinner("Roman Urdu mein khulasa tayyar ho raha hai..."):
                        st.session_state.urdu_summary = get_urdu_summary(sk, r["topic"], grade, r["content"])
                    st.rerun()

                if st.session_state.urdu_summary:
                    st.markdown(
                        f'<div style="padding:14px;background:#eafaf1;border:2px solid #27ae60;'
                        f'border-radius:12px;font-size:1.1em;line-height:1.8">'
                        f'📝 {st.session_state.urdu_summary}</div>', unsafe_allow_html=True)
                    st.caption("🔊 Neeche Sunlo dabayen — Roman Urdu awaaz mein sunein")
                    tts_button(st.session_state.urdu_summary)
                else:
                    tts_button(r["topic"] + ". " + r["content"])
                tts_urdu_install_tip()
                render_lesson_with_checkpoints(r["content"], r["topic"], sk, grade, student)

                # ---- FILL IN THE BLANK (after lesson) ----
                st.markdown("---")
                st.markdown(
                    '<div style="padding:10px 14px;background:#e8f4f8;border-left:4px solid #3498db;'
                    'border-radius:0 10px 10px 0;margin:8px 0">'
                    '<b>✏️ Likh kar jawab do — Blank bharo!</b><br>'
                    '<span style="font-size:0.85em">Ek ya do alfaaz likhein — spelling perfect honi zaroori nahi!</span>'
                    '</div>', unsafe_allow_html=True)

                # Load FITB questions for this topic (from cache or generate)
                topic_key = r["topic"]
                if st.session_state.fitb_loaded_topic != topic_key:
                    st.session_state.fitb_questions = []
                    st.session_state.fitb_results = {}
                    st.session_state.fitb_loaded_topic = topic_key
                    # Try cache first
                    cached_fitb = get_fitb_questions(topic_key, grade, r["content"])
                    if cached_fitb:
                        st.session_state.fitb_questions = cached_fitb

                fitb_qs = st.session_state.fitb_questions
                if not fitb_qs:
                    if st.button("✏️ Blank sawaal generate karo", width='stretch', key="fitb_gen"):
                        with st.spinner("Examiner Sahib blank sawaal bana rahe hain..."):
                            qs = get_fitb_questions(topic_key, grade, r["content"])
                            if qs:
                                st.session_state.fitb_questions = qs
                            else:
                                st.error("Sawaal nahi ban sake — baad mein try karo")
                        st.rerun()
                else:
                    fitb_results = st.session_state.fitb_results
                    total_correct = sum(1 for v in fitb_results.values() if v.get("correct"))

                    # Progress bar
                    answered = len(fitb_results)
                    if answered < len(fitb_qs):
                        st.progress(answered / len(fitb_qs),
                                    text=f"{answered}/{len(fitb_qs)} blank bhare")

                    for qi, blank in enumerate(fitb_qs):
                        bkey = f"fitb_{topic_key}_{qi}"
                        sentence = blank.get("sentence","")
                        answer = blank.get("answer","")
                        synonyms = blank.get("synonyms",[])
                        hint = blank.get("hint","")
                        result = fitb_results.get(str(qi))

                        # Show blank with underline style
                        display_sentence = sentence.replace("_____",
                            '<span style="display:inline-block;min-width:80px;border-bottom:2px solid #3498db;'
                            'text-align:center;padding:0 4px;color:#2980b9">_____</span>')
                        st.markdown(
                            f'<div style="padding:10px 14px;background:#f8f9fa;border-radius:8px;'
                            f'margin:6px 0;font-size:1.05em">'
                            f'<b>Sawaal {qi+1}:</b> {display_sentence}</div>',
                            unsafe_allow_html=True)

                        if result:
                            # Already answered — show result
                            bg = "#eafaf1" if result["correct"] else "#fdedec"
                            bd = "#27ae60" if result["correct"] else "#e74c3c"
                            icon = "✅" if result["correct"] else "❌"
                            st.markdown(
                                f'<div style="padding:8px 14px;background:{bg};border-radius:8px;'
                                f'border-left:4px solid {bd};margin:4px 0">'
                                f'{icon} <b>Tumhara jawab:</b> {result.get("wrote","")}<br>'
                                f'<span style="font-size:0.9em">{result.get("message","")}</span>'
                                f'{"<br><span style=font-size:0.85em;color:#888>Sahi jawab: " + answer + "</span>" if not result["correct"] else ""}'
                                f'</div>', unsafe_allow_html=True)
                        else:
                            # Show input + hint
                            if hint:
                                st.caption(f"💡 Hint: {hint}")
                            col_inp, col_btn = st.columns([4, 1])
                            with col_inp:
                                user_ans = st.text_input(
                                    f"Jawab likho",
                                    key=bkey,
                                    placeholder="Yahan likho...",
                                    label_visibility="collapsed"
                                )
                            with col_btn:
                                if st.button("✔️ Check", key=f"{bkey}_check",
                                             width='stretch'):
                                    if user_ans.strip():
                                        with st.spinner("Dekh raha hoon..."):
                                            res = check_fitb_answer(
                                                sentence, answer, synonyms,
                                                user_ans.strip(), grade
                                            )
                                        res["wrote"] = user_ans.strip()
                                        st.session_state.fitb_results[str(qi)] = res
                                        # Award stars
                                        if res.get("correct"):
                                            reg_fb = load_register()
                                            for s_fb in reg_fb["students"]:
                                                if s_fb["roll"] == student["roll"]:
                                                    s_fb["stars"] += 1
                                                    save_register(reg_fb)
                                                    break
                                        st.rerun()
                                    else:
                                        st.warning("Kuch to likho!")

                    # All answered summary
                    if answered == len(fitb_qs):
                        st.markdown(
                            f'<div style="text-align:center;padding:14px;background:#eafaf1;'
                            f'border-radius:12px;border:2px solid #27ae60;margin-top:10px">'
                            f'<b>✏️ Blanks complete!</b> {total_correct}/{len(fitb_qs)} sahi ⭐<br>'
                            f'{"🎉 Sab sahi! Bohat acha!" if total_correct == len(fitb_qs) else "Acha kaam! Quiz bhi do!"}'
                            f'</div>', unsafe_allow_html=True)

                # Show quiz result right here under the lesson
                if st.session_state.quiz_result is not None:
                    qr = st.session_state.quiz_result
                    st.markdown("---")
                    st.success(f"📝 Quiz: {qr['topic']} — Examiner Sahib")
                    st.markdown(format_options(qr["content"]))
                    reg3 = load_register()
                    for s in reg3["students"]:
                        if s["roll"] == student["roll"]: s["stars"] += 2; save_register(reg3); break
                    st.success(f"⭐ Shabash {student['name']}! +2 stars!")

        with tab2:
            if st.session_state.mcq_questions is None and not st.session_state.mcq_done:
                st.markdown("**Quiz topic chuno — Interactive MCQ!**")
                for i in range(0, len(topics), 2):
                    cols = st.columns(2)
                    for j, col in enumerate(cols):
                        if i+j < len(topics):
                            title, desc = topics[i+j]
                            diff = get_student_difficulty(student, sk, title)
                            diff_em = DIFFICULTY_EMOJI.get(diff, "🟡")
                            with col:
                                if st.button(f"📝 {title} {diff_em}", key=f"qt_{sk}_{i+j}", width='stretch'):
                                    # Check KB first, then cache, then API
                                    _, kb_quiz = load_kb_topic(sk, grade, title)
                                    if kb_quiz and "questions" in kb_quiz and len(kb_quiz["questions"]) > 0:
                                        st.session_state.mcq_questions = kb_quiz["questions"]
                                        st.session_state.mcq_topic = kb_quiz.get("title", title)
                                        st.session_state.mcq_current = 0
                                        st.session_state.mcq_answers = []
                                        st.session_state.mcq_done = False
                                        st.rerun()
                                    else:
                                        cached = get_cached_quiz(sk, title, grade)
                                        if cached:
                                            st.session_state.mcq_questions = cached["questions"]
                                            st.session_state.mcq_topic = cached.get("title", title)
                                            st.session_state.mcq_current = 0
                                            st.session_state.mcq_answers = []
                                            st.session_state.mcq_done = False
                                            st.rerun()
                                        else:
                                            with st.spinner(f"Examiner Sahib quiz tayyar kar rahe hain ({diff})..."):
                                                req = f"Grade {grade} {subj['name']} quiz about '{title}': {desc}. DIFFICULTY: {diff.upper()}. 5 MCQ questions. ROMAN URDU ONLY."
                                                ans = run_agent(MCQ_EXAMINER_PROMPT, req + student_context(student), 3000)
                                                try:
                                                    quiz_data = parse_json(ans)
                                                    if "questions" in quiz_data and len(quiz_data["questions"]) > 0:
                                                        st.session_state.mcq_questions = quiz_data["questions"]
                                                        st.session_state.mcq_topic = quiz_data.get("title", title)
                                                        st.session_state.mcq_current = 0
                                                        st.session_state.mcq_answers = []
                                                        st.session_state.mcq_done = False
                                                        save_record("quizzes", req, ans, student)
                                                        save_quiz_to_cache(sk, title, grade, quiz_data)
                                                    else:
                                                        st.error("Quiz format error!")
                                                except:
                                                    st.error("Quiz parse error!")
                                            st.rerun()
                                st.caption(desc)

            elif st.session_state.mcq_questions and not st.session_state.mcq_done:
                qi = st.session_state.mcq_current
                questions = st.session_state.mcq_questions
                q = questions[qi]
                total = len(questions)

                st.markdown(f"**📝 {st.session_state.mcq_topic}**")
                st.progress((qi) / total, text=f"Sawal {qi+1} / {total}")

                st.markdown(
                    f'<div style="padding:16px;background:#f0f8ff;border-radius:12px;'
                    f'border:2px solid #3498db;margin:8px 0">'
                    f'<h3>Sawal {qi+1}: {q["q"]}</h3></div>',
                    unsafe_allow_html=True)

                correct = q.get("correct", "a").lower()
                options = {"a": q.get("a",""), "b": q.get("b",""), "c": q.get("c",""), "d": q.get("d","")}

                for key, text in options.items():
                    emoji = "🔵" if key=="a" else "🟢" if key=="b" else "🟡" if key=="c" else "🔴"
                    st.button(
                        f"{emoji} {key.upper()}: {text}", key=f"mcq_{qi}_{key}",
                        width='stretch',
                        on_click=mcq_answer, args=(key, correct, qi)
                    )

            elif st.session_state.mcq_done:
                answers = st.session_state.mcq_answers
                questions = st.session_state.mcq_questions
                score = sum(1 for a in answers if a["right"])
                total = len(questions)
                stars_earned = score

                # Adaptive: update difficulty for this topic
                old_diff, new_diff = update_student_difficulty(
                    student["roll"], sk, st.session_state.mcq_topic, score
                )
                if score >= 3:
                    mark_topic_done(student["roll"], sk, st.session_state.mcq_topic)
                    _qr = st.session_state.get("quiz_result")
                    if _qr and _qr.get("topic"):
                        mark_topic_done(student["roll"], sk, _qr["topic"])
                diff_changed = old_diff != new_diff

                reg_q = load_register()
                for s in reg_q["students"]:
                    if s["roll"] == student["roll"]:
                        s["stars"] += stars_earned
                        save_register(reg_q)
                        new_total = s["stars"]
                        break

                # Track today's progress
                st.session_state.quizzes_today += 1
                st.session_state.stars_today += stars_earned

                # Save wrong answers to Ghalti Copy, clear correct ones
                wrong_qs = [
                    questions[a["qi"]]
                    for a in answers
                    if not a["right"] and a["qi"] < len(questions)
                ]
                correct_qs = [
                    questions[a["qi"]]["q"]
                    for a in answers
                    if a["right"] and a["qi"] < len(questions)
                ]
                if wrong_qs:
                    add_to_ghalti(student["roll"], sk, st.session_state.mcq_topic, wrong_qs)

                # If student scored 4-5/5 → topic mastered → clear ALL ghalti for this topic
                if score >= 4:
                    removed = clear_ghalti_topic(student["roll"], sk, st.session_state.mcq_topic)
                    if removed:
                        st.success(f"🌟 Shabash! {removed} ghalti(yan) Ghalti Copy se hata di gayin — topic master ho gaya!")
                elif correct_qs:
                    # Partially correct — remove only the questions answered correctly
                    removed = clear_ghalti_correct_answers(student["roll"], sk, st.session_state.mcq_topic, correct_qs)
                    if removed:
                        st.info(f"✅ {removed} sahi jawab Ghalti Copy se hata diye gaye!")

                # Show ghalti notification for remaining wrong answers
                if wrong_qs and score < 4:
                    ghalti_total = get_ghalti_count(student["roll"])
                    st.warning(
                        f"📒 **{len(wrong_qs)} ghalat jawab Ghalti Copy mein save ho gaye!** "
                        f"Tab 3 mein review karo!"
                    )
                milestones = {5: "5 Stars!", 10: "10 Stars! Double digits!", 
                              15: "Explorer level!", 25: "25 Stars! Quarter century!",
                              30: "Commander level!", 50: "ASTRONAUT! Top level!"}
                for threshold, msg in milestones.items():
                    if new_total >= threshold and (new_total - stars_earned) < threshold:
                        st.session_state.celebration = {"stars": threshold, "msg": msg}
                        break
                if score == total:
                    msg, color = "🏆 PERFECT! Mashallah! 🏆", "#27ae60"
                elif score >= 4:
                    msg, color = "🌟 Bohat acha!", "#2ecc71"
                elif score >= 3:
                    msg, color = "👍 Acha! Keep going!", "#f39c12"
                else:
                    msg, color = "💪 Practice makes perfect!", "#e74c3c"
                st.markdown(
                    f'<div style="text-align:center;padding:20px;background:linear-gradient(135deg,#fef9e7,#eafaf1);'
                    f'border-radius:16px;border:3px solid {color}">'
                    f'<h2>{msg}</h2><p style="font-size:2em"><b>{score}/{total}</b></p>'
                    f'<p style="font-size:1.3em">⭐ +{stars_earned} stars!</p></div>', unsafe_allow_html=True)

                # Adaptive feedback message
                if diff_changed:
                    old_em = DIFFICULTY_EMOJI.get(old_diff, "🟡")
                    new_em = DIFFICULTY_EMOJI.get(new_diff, "🟡")
                    if new_diff == "hard":
                        st.success(f"📈 Level UP! {old_em} {old_diff} → {new_em} {new_diff} — Tum ready ho mushkil sawaalon ke liye!")
                    elif new_diff == "easy":
                        st.info(f"📉 {old_em} {old_diff} → {new_em} {new_diff} — Koi baat nahi! Pehle basics mazboot karein, phir aage badhein!")
                else:
                    st.caption(f"Level: {DIFFICULTY_EMOJI.get(new_diff, '🟡')} {new_diff} — same level practice")
                for i, (q, a) in enumerate(zip(questions, answers)):
                    icon = "✅" if a["right"] else "❌"
                    bg = "#eafaf1" if a["right"] else "#fdedec"
                    bd = "#27ae60" if a["right"] else "#e74c3c"
                    chose_t = q.get(a["chose"], "?")
                    corr_t = q.get(a["correct"], "?")
                    extra = "" if a["right"] else f" — Sahi: <b>{a['correct'].upper()}: {corr_t}</b>"
                    st.markdown(
                        f'<div style="padding:10px;margin:6px 0;background:{bg};border-radius:8px;border-left:4px solid {bd}">'
                        f'<b>{icon} Q{i+1}: {q["q"]}</b><br>'
                        f'Tumhara jawab: <b>{a["chose"].upper()}: {chose_t}</b>{extra}'
                        f'<br><i>{q.get("explanation","")}</i></div>', unsafe_allow_html=True)
                st.balloons()
                st.markdown("---")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📝 Aur quiz!", width='stretch'):
                        reset_mcq(); st.rerun()
                with c2:
                    if st.button("🏫 Classroom", width='stretch'):
                        reset_mcq(); go(screen="classroom"); st.rerun()

        # ========================
        #  TAB 3: GHALTI COPY
        # ========================
        with tab3:
            due = get_ghalti_due(student["roll"])
            all_gc = load_ghalti().get(str(student["roll"]), [])

            if not all_gc:
                st.markdown(
                    '<div style="text-align:center;padding:30px;background:#eafaf1;border-radius:12px;border:2px solid #27ae60">'
                    '<h3>🌟 Shabash! Ghalti Copy khali hai!</h3>'
                    '<p>Abhi tak koi ghalti save nahi hui. Quiz do aur ghalat jawab yahin aayenge!</p>'
                    '</div>', unsafe_allow_html=True)
            else:
                st.markdown(
                    f'<div style="padding:12px;background:#fef9e7;border-radius:10px;border:2px solid #f39c12">'
                    f'<b>📒 Ghalti Copy</b> — {student["name"]} ki ghaltiyan<br>'
                    f'<span style="font-size:0.9em">Kul ghaltiyan: <b>{len(all_gc)}</b> | '
                    f'Aaj review ke liye: <b>{len(due)}</b></span>'
                    f'</div>', unsafe_allow_html=True)
                st.markdown("")

                if not due:
                    st.info("✅ Aaj ke review complete! Kal aur ghaltiyan review hongi.")
                    st.markdown("**Saari ghaltiyan:**")
                    for e in all_gc:
                        subj_name = SUBJECTS.get(e["subject"], {}).get("name", e["subject"])
                        st.caption(f"• {subj_name} — {e['topic']}: {e['question']['q']}")
                else:
                    # Show ghalti questions one by one
                    if not st.session_state.ghalti_mode:
                        st.markdown(f"**{len(due)} sawaal aaj review ke liye hain:**")
                        for i, e in enumerate(due):
                            subj_name = SUBJECTS.get(e["subject"], {}).get("name", e["subject"])
                            st.markdown(
                                f'<div style="padding:8px 12px;margin:4px 0;background:#fdedec;'
                                f'border-left:4px solid #e74c3c;border-radius:0 8px 8px 0">'
                                f'<b>{i+1}.</b> {subj_name} — <i>{e["topic"]}</i><br>'
                                f'<span style="font-size:0.9em">{e["question"]["q"]}</span>'
                                f'</div>', unsafe_allow_html=True)
                        if st.button("📒 Ghaltiyan dobara karo!", width='stretch', type="primary"):
                            st.session_state.ghalti_mode = True
                            st.session_state.ghalti_idx = 0
                            st.session_state.ghalti_answers = []
                            st.rerun()
                    else:
                        idx = st.session_state.ghalti_idx
                        if idx < len(due):
                            e = due[idx]
                            q = e["question"]
                            subj_name = SUBJECTS.get(e["subject"], {}).get("name", e["subject"])
                            st.progress(idx / len(due), text=f"Ghalti {idx+1} / {len(due)}")
                            st.markdown(
                                f'<div style="padding:16px;background:#fef9e7;border-radius:12px;'
                                f'border:2px solid #f39c12;margin:8px 0">'
                                f'<p style="font-size:0.85em;color:#888">{subj_name} — {e["topic"]}</p>'
                                f'<h3>🔄 {q["q"]}</h3></div>', unsafe_allow_html=True)
                            correct = q.get("correct","a").lower()
                            for opt_key, opt_emoji in [("a","🔵"),("b","🟢"),("c","🟡"),("d","🔴")]:
                                opt_text = q.get(opt_key, "")
                                if st.button(f"{opt_emoji} {opt_key.upper()}: {opt_text}",
                                             key=f"gc_{idx}_{opt_key}", width='stretch'):
                                    is_right = opt_key == correct
                                    mark_ghalti_reviewed(student["roll"], q["q"], is_right)
                                    st.session_state.ghalti_answers.append({"right": is_right, "q": q["q"]})
                                    if is_right and student["roll"]:
                                        reg_g = load_register()
                                        for s_g in reg_g["students"]:
                                            if s_g["roll"] == student["roll"]:
                                                s_g["stars"] += 1; save_register(reg_g); break
                                    st.session_state.ghalti_idx += 1
                                    st.rerun()
                        else:
                            # Review complete
                            correct_count = sum(1 for a in st.session_state.ghalti_answers if a["right"])
                            total_done = len(st.session_state.ghalti_answers)
                            st.markdown(
                                f'<div style="text-align:center;padding:20px;background:#eafaf1;'
                                f'border-radius:16px;border:3px solid #27ae60">'
                                f'<h2>🌟 Ghalti Copy Review Mukammal!</h2>'
                                f'<p style="font-size:1.5em"><b>{correct_count}/{total_done}</b> sahi!</p>'
                                f'<p>⭐ +{correct_count} stars milein!</p>'
                                f'</div>', unsafe_allow_html=True)
                            for a in st.session_state.ghalti_answers:
                                icon = "✅" if a["right"] else "❌"
                                st.caption(f"{icon} {a['q']}")
                            if st.button("📒 Wapas ghalti copy", width='stretch'):
                                st.session_state.ghalti_mode = False
                                st.session_state.ghalti_idx = 0
                                st.session_state.ghalti_answers = []
                                st.rerun()

    # ========================
    #  JUMA TEST SCREEN
    # ========================
    elif screen == "juma_test":
        qs = st.session_state.juma_questions or []
        if not qs:
            st.warning("Juma Test ke liye sawaal nahi mile. Pehle kuch quizzes do taake KB bhar sake!")
            if st.button("🏫 Hallway wapas"):
                go(screen="hallway"); st.rerun()
        elif not st.session_state.juma_done:
            idx = st.session_state.juma_current
            if idx < len(qs):
                q = qs[idx]
                st.markdown(
                    f'<div style="text-align:center;padding:12px;background:#fff3cd;'
                    f'border-radius:12px;border:3px solid #f39c12;margin-bottom:10px">'
                    f'<h2>📋 Juma Test — Hafta bhar ka Imtehaan</h2>'
                    f'<p>10 sawaal • 5 subjects • {student["name"]} — Grade {grade}</p>'
                    f'</div>', unsafe_allow_html=True)
                st.progress(idx / len(qs), text=f"Sawaal {idx+1} / {len(qs)}")
                subj_badge = q.get("_subject","")
                st.markdown(
                    f'<div style="padding:16px;background:#f8f9fa;border-radius:12px;'
                    f'border:2px solid #f39c12;margin:8px 0">'
                    f'<p style="font-size:0.82em;color:#888;margin:0">'
                    f'📚 {subj_badge} — {q.get("_topic","")}</p>'
                    f'<h3 style="margin:8px 0">Sawaal {idx+1}: {q["q"]}</h3>'
                    f'</div>', unsafe_allow_html=True)
                correct = q.get("correct","a").lower()
                for opt_key, opt_emoji in [("a","🔵"),("b","🟢"),("c","🟡"),("d","🔴")]:
                    opt_text = q.get(opt_key,"")
                    if st.button(f"{opt_emoji} {opt_key.upper()}: {opt_text}",
                                 key=f"jt_{idx}_{opt_key}", width='stretch'):
                        is_right = opt_key == correct
                        st.session_state.juma_answers.append({
                            "qi": idx, "chose": opt_key, "correct": correct,
                            "right": is_right, "q": q["q"],
                            "subject": q.get("_subject",""),
                            "topic": q.get("_topic",""),
                            "subj_key": q.get("_subj_key",""),
                            "explanation": q.get("explanation","")
                        })
                        if idx + 1 >= len(qs):
                            st.session_state.juma_done = True
                        else:
                            st.session_state.juma_current += 1
                        st.rerun()
            else:
                st.session_state.juma_done = True
                st.rerun()
        else:
            # JUMA TEST RESULTS
            answers = st.session_state.juma_answers
            score = sum(1 for a in answers if a["right"])
            total = len(answers)
            # Save result
            mark_juma_done(student["roll"], score, total)
            # Award stars (2 per correct, bonus for high score)
            bonus = 5 if score == total else 3 if score >= 8 else 0
            stars_earned = score * 2 + bonus
            reg_jt = load_register()
            for s in reg_jt["students"]:
                if s["roll"] == student["roll"]:
                    s["stars"] += stars_earned; save_register(reg_jt); break

            # Grade message
            if score == total:
                msg, color = "🏆 PERFECT! Hafta bhar ki mehnat rang layi! 🏆", "#27ae60"
            elif score >= 8:
                msg, color = "🌟 Bohat acha! Tum bohat hoshiyar ho!", "#2ecc71"
            elif score >= 6:
                msg, color = "👍 Acha kaam! Aur thodi practice chahiye!", "#f39c12"
            else:
                msg, color = "💪 Koi baat nahi — agli baar aur mehnat karein!", "#e74c3c"

            st.markdown(
                f'<div style="text-align:center;padding:24px;background:#fffbea;'
                f'border-radius:20px;border:4px solid #f39c12">'
                f'<h1>📋 Juma Test — Nateeja!</h1>'
                f'<h2>{msg}</h2>'
                f'<p style="font-size:2.5em"><b>{score}/{total}</b></p>'
                f'<p style="font-size:1.3em">⭐ +{stars_earned} stars!'
                f'{" (Bonus +5 perfect score!)" if bonus == 5 else " (Bonus +3!)" if bonus == 3 else ""}</p>'
                f'</div>', unsafe_allow_html=True)
            st.balloons()
            st.markdown("---")
            st.markdown("**Jawab-naama (answer review):**")

            # Group results by subject
            subj_results = {}
            for a in answers:
                sk2 = a.get("subj_key","")
                subj_results.setdefault(sk2, []).append(a)
                # Save wrong answers to Ghalti Copy
                if not a["right"] and sk2:
                    wrong_q = next((q for q in (st.session_state.juma_questions or [])
                                   if q.get("q") == a["q"]), None)
                    if wrong_q:
                        add_to_ghalti(student["roll"], sk2, a["topic"], [wrong_q])

            for sk2, res in subj_results.items():
                subj_name = SUBJECTS.get(sk2, {}).get("name", sk2)
                subj_score = sum(1 for r in res if r["right"])
                st.markdown(f"**{SUBJECTS.get(sk2,{}).get('emoji','📚')} {subj_name}: {subj_score}/{len(res)}**")
                for a in res:
                    icon = "✅" if a["right"] else "❌"
                    st.markdown(
                        f'<div style="padding:8px 12px;margin:3px 0;background:'
                        f'{"#eafaf1" if a["right"] else "#fdedec"};border-radius:8px;'
                        f'border-left:3px solid {"#27ae60" if a["right"] else "#e74c3c"}">'
                        f'{icon} {a["q"]}<br>'
                        f'<small>{a.get("explanation","")}</small>'
                        f'</div>', unsafe_allow_html=True)

            st.markdown("---")
            if st.button("🏫 Hallway wapas", width='stretch', type="primary"):
                st.session_state.juma_questions = None
                st.session_state.juma_answers = []
                st.session_state.juma_done = False
                go(screen="hallway"); st.rerun()

    # ========================
    #  CHAT
    # ========================
    elif screen == "chat":
        if st.button("⬅️ Wapas hallway"):
            go(screen="hallway"); st.rerun()
        st.markdown('<h2 style="text-align:center">💬 Class Teacher se baat karo</h2>', unsafe_allow_html=True)

        # Daily chat limit — 8 messages per student per day (free limit)
        DAILY_CHAT_LIMIT = 8
        chats_today = sum(
            1 for m in st.session_state.chat_history if m["role"] == "user"
        )
        remaining = DAILY_CHAT_LIMIT - chats_today

        if remaining <= 2 and remaining > 0:
            st.warning(f"⚠️ Sirf {remaining} sawal bacha hai aaj ke liye!")
        elif remaining <= 0:
            st.markdown(
                '<div style="text-align:center;padding:16px;background:#fdedec;border-radius:12px;border:2px solid #e74c3c">'
                '<h3>🔔 Aaj ke sawalaat mukammal!</h3>'
                '<p>Class Teacher ne aaj bohat madad ki! Kal aur sawal poochho.</p>'
                '<p>Abhi <b>sabaq parho</b> ya <b>quiz do</b> — wahan bhi jawab milte hain!</p>'
                '</div>', unsafe_allow_html=True)

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

        if remaining > 0:
            q = st.chat_input(f"Sawal likho... ({remaining} bacha hai aaj)")
            if q:
                st.session_state.chat_history.append({"role":"user","content":q})
                with st.chat_message("user"): st.markdown(q)
                with st.chat_message("assistant"):
                    with st.spinner("Class Teacher soch rahi hain..."):
                        ans = run_agent(CLASS_TEACHER_PROMPT, f"Student: {q}{student_context(student)}", 1500)
                        save_record("class_teacher", q, ans, student)
                    st.markdown(ans)
                st.session_state.chat_history.append({"role":"assistant","content":ans})

    # ========================
    #  REPORT CARD
    # ========================
    elif screen == "report":
        if st.button("⬅️ Wapas hallway"):
            go(screen="hallway"); st.rerun()
        st.markdown('<h2 style="text-align:center">🏆 Report Card</h2>', unsafe_allow_html=True)
        stars = student["stars"]
        streak = get_streak(student)
        s_emoji, s_msg = streak_badge(streak)
        if stars >= 50: lv, bg = "Astronaut 🚀", "🚀"
        elif stars >= 30: lv, bg = "Commander 🎖️", "🎖️"
        elif stars >= 15: lv, bg = "Explorer 🧭", "🧭"
        else: lv, bg = "Pilot ✈️", "✈️"
        st.markdown(
            f'<div style="text-align:center;padding:20px;border:3px solid #f39c12;border-radius:16px;background:#fffbea">'
            f'<h2>{bg} {student["name"]}</h2><p style="font-size:1.3em"><b>Level: {lv}</b></p>'
            f'<p>Roll {student["roll"]} | Grade {grade} | {student["section"]}</p><hr>'
            f'<p style="font-size:1.5em">⭐ <b>{stars}</b> Stars</p>'
            f'<p style="font-size:1.3em">{s_emoji} <b>{streak} din streak</b> — {s_msg}</p>'
            f'<p>📅 Hazri: <b>{len(student["attendance"])}</b> din | Joined: {student["joined"]}</p></div>', unsafe_allow_html=True)
        if stars < 15: nl, nd = "Explorer 🧭", 15
        elif stars < 30: nl, nd = "Commander 🎖️", 30
        elif stars < 50: nl, nd = "Astronaut 🚀", 50
        else: nl, nd = None, None
        if nl:
            st.markdown(f"**Next: {nl}** ({stars}/{nd})"); st.progress(min(stars/nd,1.0))
        else:
            st.success("🚀 TOP LEVEL! Astronaut!")

    # ========================
    #  CHHUTI SCREEN (end of day)
    # ========================
    elif screen == "chhuti":
        streak = get_streak(student)
        s_emoji, s_msg = streak_badge(streak)

        st.markdown(
            f'<div style="text-align:center;padding:24px;background:linear-gradient(135deg,#fef9e7,#f5eef8,#e8f8f5);'
            f'border-radius:20px;border:3px solid #f39c12">'
            f'<h1>🔔 Chhuti ka waqt! 🔔</h1>'
            f'<h2>Allah Hafiz, {student["name"]}!</h2>'
            f'<p style="font-size:1.2em">Aaj ka din bohat acha raha!</p>'
            f'</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<h3 style="text-align:center">📊 Aaj ka report</h3>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                f'<div style="text-align:center;padding:16px;background:#e8f8f5;border-radius:12px;border:2px solid #1abc9c">'
                f'<p style="font-size:2em;margin:0">📖</p>'
                f'<p style="font-size:1.8em;margin:0"><b>{st.session_state.lessons_today}</b></p>'
                f'<p>Sabaq parhe</p></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(
                f'<div style="text-align:center;padding:16px;background:#fef9e7;border-radius:12px;border:2px solid #f39c12">'
                f'<p style="font-size:2em;margin:0">📝</p>'
                f'<p style="font-size:1.8em;margin:0"><b>{st.session_state.quizzes_today}</b></p>'
                f'<p>Quiz diye</p></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(
                f'<div style="text-align:center;padding:16px;background:#f5eef8;border-radius:12px;border:2px solid #9b59b6">'
                f'<p style="font-size:2em;margin:0">⭐</p>'
                f'<p style="font-size:1.8em;margin:0"><b>{st.session_state.stars_today}</b></p>'
                f'<p>Stars kamaaye</p></div>', unsafe_allow_html=True)

        st.markdown("---")

        # Streak status
        st.markdown(
            f'<div style="text-align:center;padding:14px;background:#fffbea;border-radius:12px;border:2px solid #f39c12">'
            f'<p style="font-size:1.5em;margin:0">{s_emoji} <b>{streak} din streak</b> — {s_msg}</p>'
            f'<p>Total stars: ⭐ {student["stars"]} | Total hazri: 📅 {len(student["attendance"])} din</p>'
            f'</div>', unsafe_allow_html=True)

        # Motivational message based on activity
        if st.session_state.lessons_today >= 3 and st.session_state.quizzes_today >= 2:
            st.success("🏆 Mashallah! Aaj bohat mehnat ki! Ammi Abu ko zaroor bataana!")
        elif st.session_state.lessons_today >= 1:
            st.info("👍 Acha kaam kiya aaj! Kal aur zyada seekhna!")
        else:
            st.warning("📖 Aaj koi sabaq nahi parha? Koi baat nahi — kal inshallah!")

        st.markdown("---")

        # Tomorrow preview
        import datetime as dt
        tomorrow = (dt.date.today() + dt.timedelta(days=1)).weekday()
        tt_tmrw = TIMETABLES[tomorrow]
        tmrw_name = DAY_NAMES_UR[tomorrow]
        st.markdown(f"**📅 Kal ({tmrw_name}) ka schedule:**")
        for i, sk2 in enumerate(tt_tmrw):
            subj2 = SUBJECTS[sk2]
            st.caption(f"Period {i+1} ({PERIOD_TIMES[i]}): {subj2['emoji']} {subj2['name']}")

        st.markdown("---")

        # ---- HOMEWORK DIARY ----
        hw_today = get_todays_homework(student["roll"])
        last_lesson = st.session_state.get("lesson_result")
        last_subject = st.session_state.get("stu_subject","ai")

        if hw_today:
            hw = hw_today[-1]
            done_color = "#eafaf1" if hw.get("done") else "#fff8e1"
            done_border = "#27ae60" if hw.get("done") else "#f39c12"
            done_icon = "✅" if hw.get("done") else "📓"
            st.markdown(
                f'<div style="padding:16px;background:{done_color};border-radius:14px;'
                f'border:3px solid {done_border}">'
                f'<h3>{done_icon} Aaj ka Homework</h3>'
                f'<p style="font-size:1.1em"><b>{hw["subject"]}</b> — {hw["topic"]}</p>'
                f'<p style="font-size:1.15em;background:#fff;padding:10px;border-radius:8px">'
                f'📝 {hw["task"]}</p>'
                f'<p style="font-size:0.85em;color:#888">Kal assembly mein poochha jayega!</p>'
                f'</div>', unsafe_allow_html=True)
            if not hw.get("done"):
                if st.button("✅ Homework ho gaya!", width='stretch', type="primary"):
                    mark_hw_done(student["roll"], hw["date"])
                    reg_hw = load_register()
                    for s_hw in reg_hw["students"]:
                        if s_hw["roll"] == student["roll"]:
                            s_hw["stars"] += 3
                            save_register(reg_hw)
                            break
                    st.success("Shabash! +3 stars! Kal assembly mein batana!")
                    st.rerun()
        elif last_lesson:
            # Auto-assign homework from today's last lesson
            subj_name = SUBJECTS.get(last_subject, {}).get("name", "")
            hw = assign_homework(
                student["roll"], grade,
                last_lesson["topic"], subj_name
            )
            if hw:
                st.markdown(
                    f'<div style="padding:16px;background:#fff8e1;border-radius:14px;'
                    f'border:3px solid #f39c12">'
                    f'<h3>📓 Ghar ka Kaam (Homework)</h3>'
                    f'<p><b>{hw["subject"]}</b> — {hw["topic"]}</p>'
                    f'<p style="font-size:1.15em;background:#fff;padding:10px;border-radius:8px">'
                    f'📝 {hw["task"]}</p>'
                    f'<p style="font-size:0.85em;color:#888">Kal assembly mein poochha jayega — tayaar raho!</p>'
                    f'</div>', unsafe_allow_html=True)
        else:
            st.info("📓 Homework: Aaj koi sabaq nahi parha — kal zaroor padhna!")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("🏫 Wapas school!", width='stretch'):
                go(screen="hallway"); st.rerun()
        with c2:
            if st.button("🚪 Ghar jaao (logout)", width='stretch'):
                reset_student_session()
                st.session_state.lessons_today = 0
                st.session_state.quizzes_today = 0
                st.session_state.stars_today = 0
                go(mode="door"); st.rerun()

    # ========================
    #  CELEBRATION (milestone popup)
    # ========================
    if st.session_state.celebration:
        cel = st.session_state.celebration
        st.balloons()
        st.markdown(
            f'<div style="text-align:center;padding:24px;background:linear-gradient(135deg,#fffbea,#fef9e7);'
            f'border-radius:20px;border:4px solid #f39c12;margin:12px 0">'
            f'<h1>🎉🎊 MUBARAK HO! 🎊🎉</h1>'
            f'<p style="font-size:2em">⭐ {cel["stars"]} Stars!</p>'
            f'<h2>{cel["msg"]}</h2>'
            f'<p style="font-size:1.2em">{student["name"]} ne kamaal kar diya!</p>'
            f'<p>Ammi Abu ko batao — unhe bhi khushi hogi!</p>'
            f'</div>', unsafe_allow_html=True)
        if st.button("Shukriya! Aage barhein!", width='stretch'):
            st.session_state.celebration = None
            st.rerun()


# =====================================================================
#  ADMIN MODE
# =====================================================================
elif st.session_state.mode == "admin":
    if st.button("🚪 Wapas Main Door"):
        go(mode="door"); st.rerun()

    with st.sidebar:
        st.header("🎒 Student Desk")
        names = ["— select —"] + [f"{s['name']} (Roll {s['roll']}, Gr {s['grade']})" for s in register["students"]]

        # Auto-select if Edit button was clicked from Register
        default_idx = 0
        if "_select_roll" in st.session_state:
            sel_roll = st.session_state.pop("_select_roll")
            for i, s in enumerate(register["students"]):
                if s["roll"] == sel_roll:
                    default_idx = i + 1
                    break

        picked = st.selectbox("Student", names, index=default_idx)
        student = None
        if picked != "— select —":
            student = register["students"][names.index(picked)-1]
        if st.session_state.get("edit_msg"): st.success(st.session_state.pop("edit_msg"))

        with st.expander("🆕 Naya Daakhla"):
            st.text_input("Naam", key="adm_name")
            st.selectbox("Grade (Class 1-5 only)", list(range(1, 6)), key="adm_grade")
            st.button("Admit karo!", on_click=do_admit)
            if st.session_state.get("admit_msg"): st.success(st.session_state.pop("admit_msg")); st.balloons()

        if student:
            st.markdown(
                f'<div style="border:3px solid #f39c12;border-radius:12px;padding:10px;background:#fffbea;text-align:center">'
                f'<b>🐱 Student ID</b><br><b style="font-size:1.2em">{student["name"]}</b><br>'
                f'Roll {student["roll"]} | Grade {student["grade"]} | {student["section"]}<br>'
                f'⭐ {student["stars"]} | {len(student["attendance"])} days</div>', unsafe_allow_html=True)
            if today() not in student["attendance"]:
                if st.button(f"🔔 Hazri — {student['name']}"):
                    mark_attendance(register, student); st.success("Hazir! +1 ⭐"); st.balloons()
            else: st.caption("✅ Hazri done")
            with st.expander("✏️ Edit Student"):
                rk = student["roll"]
                st.text_input("Naam", value=student["name"], key=f"e_name_{rk}")
                st.button("💾 Save", key=f"e_save_{rk}", on_click=do_edit, args=(rk,))
                st.write(f"**Grade** (now: {student['grade']}) — Class 1-5 only")
                gc = st.columns(5)
                for i, g in enumerate(range(1, 6)):
                    gc[i].button(str(g), key=f"g{g}_{rk}", on_click=set_grade, args=(rk, g),
                                 type="primary" if g == student["grade"] else "secondary")
                st.write(f"**Section** (now: {student['section']})")
                sc = st.columns(2)
                for i, sec in enumerate(SECTIONS):
                    sc[i%2].button(sec, key=f"s{sec}_{rk}", on_click=set_section, args=(rk, sec),
                                   type="primary" if sec == student["section"] else "secondary")
                st.markdown("---")
                st.write("**🗑️ Student delete karo**")
                st.caption(f"⚠️ {student['name']} (Roll {rk}) hamesha ke liye delete ho jayega!")
                st.button(
                    f"🗑️ Delete {student['name']}", key=f"del_{rk}",
                    on_click=delete_student, args=(rk,),
                    type="secondary"
                )

        with st.expander("📋 Register"):
            if register["students"]:
                for s in register["students"]:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{s['roll']}. {s['name']}** — Gr {s['grade']} {s['section']} | ⭐{s['stars']}")
                    with col2:
                        if st.button("✏️ Edit", key=f"reg_edit_{s['roll']}", width='stretch'):
                            # Select this student in the dropdown
                            st.session_state["_select_roll"] = s["roll"]
                            st.rerun()
                st.download_button("⬇️ Download", json.dumps(register, ensure_ascii=False, indent=2), file_name="students.json")
        st.divider()

        # ------------------------------------------------------------------
        # BACKUP / RESTORE — cloud school ke liye zaroori
        # Student ka record kabhi GitHub par nahi jaata. Isi liye purana
        # record yahan se upload kar ke wapas laaya jaata hai.
        # ------------------------------------------------------------------
        st.header("💾 Backup / Restore")
        st.caption("Cloud par record permanent disk mein mehfooz rehta hai. "
                   "Phir bhi hafte mein ek baar backup download kar lein — "
                   "yeh aap ka apna copy hai, kisi aur par bharosa nahi.")
        _b1, _b2 = st.columns(2)
        with _b1:
            try:
                _hw_now = (json.load(open(HW_FILE, encoding="utf-8"))
                           if os.path.exists(HW_FILE) else {})
            except Exception:
                _hw_now = {}
            st.download_button(
                "⬇️ Poora backup download karein",
                json.dumps({"students": register.get("students", []),
                            "ghalti": load_ghalti(),
                            "homework": _hw_now,
                            "saved_at": datetime.datetime.now().isoformat()},
                           ensure_ascii=False, indent=2),
                file_name=f"ai4kids_backup_{datetime.date.today()}.json",
                mime="application/json", width='stretch')
        with _b2:
            _up = st.file_uploader("⬆️ Backup file chunein", type=["json"],
                                   key="restore_up",
                                   help="Purana backup ya students.json upload karein")
            if _up is not None:
                if st.button("♻️ Restore karein — purana record wapas",
                             width='stretch', type="primary"):
                    try:
                        _raw = json.loads(_up.getvalue().decode("utf-8"))
                        _studs = _raw.get("students") if isinstance(_raw, dict) else _raw
                        if not isinstance(_studs, list):
                            st.error("Is file mein students ka record nahi mila.")
                        else:
                            save_register({"students": _studs})
                            if isinstance(_raw, dict):
                                if isinstance(_raw.get("ghalti"), dict):
                                    save_ghalti(_raw["ghalti"])
                                if isinstance(_raw.get("homework"), dict):
                                    with open(HW_FILE, "w", encoding="utf-8") as _hf:
                                        json.dump(_raw["homework"], _hf,
                                                  ensure_ascii=False, indent=2)
                            st.success(f"✅ {len(_studs)} students restore ho gaye!")
                            st.rerun()
                    except Exception as _e:
                        st.error(f"Restore nahi ho saka: {_e}")

        st.divider()
        if os.path.exists(LESSON_BANK_PATH):
            if st.button("📚 Lesson Bank & Curriculum", width='stretch', key="admin_lb"):
                st.session_state.view_lessonbank = not st.session_state.get("view_lessonbank", False)
                st.rerun()
        if os.path.exists(CURRICULUM_PATH):
            if st.button("📖 Curriculum — Class 1-5 (FBISE/SNC)", width='stretch', key="admin_cur"):
                st.session_state.view_curriculum = not st.session_state.get("view_curriculum", False)
                st.rerun()
        render_html_viewers()
        st.divider()
        st.header("🗄️ Record Room")
        found = False
        if os.path.isdir(RECORD_ROOM):
            for dept in sorted(os.listdir(RECORD_ROOM)):
                dp = os.path.join(RECORD_ROOM, dept)
                if not os.path.isdir(dp): continue
                files = sorted(os.listdir(dp), reverse=True)
                if files:
                    found = True; st.subheader(dept.replace("_"," ").title())
                    for fn in files[:10]:
                        fp = os.path.join(dp, fn)
                        _title, _date = record_label(fp, fn)
                        with st.expander(_title):
                            if _date:
                                st.caption(f"🗓️ {_date}")
                            with open(fp, encoding="utf-8") as f: ct = f.read()
                            st.markdown(format_options(ct)); st.download_button("⬇️", ct, file_name=fn, key=fp)
        if not found: st.info("Record room khali hai")

    st.caption("Quick start:")
    c1,c2,c3 = st.columns(3)
    preset = None
    if c1.button("📖 Lesson"): preset = f"Grade {student['grade'] if student else 3} lesson: How do computers learn?"
    if c2.button("📝 Quiz"): preset = f"Grade {student['grade'] if student else 5} quiz about AI."
    if c3.button("👨‍👩‍👧 Parent"): preset = "Parent: admission process kya hai?"

    with st.expander("🔌 Inference endpoint (ai_config.json)"):
        _s = ai_config.config_summary()
        st.markdown(
            f"**{_s['label']}**  \n"
            f"Base URL: `{_s['base_url']}`  \n"
            f"Model: `{_s['model']}`  \n"
            f"API key: `{_s['api_key']}`  \n"
            f"TTS: `{_s['tts_model']}` (voice `{_s['tts_voice']}`) — "
            f"{'ON' if _s['tts_enabled'] else 'OFF (browser awaaz)'}  \n"
            f"TTS endpoint: `{_s['tts_base_url']}`"
            f"{'  ← ALAG provider' if _s['tts_separate'] else ''}  \n"
            f"TTS key: `{_s['tts_api_key']}`  \n"
            f"Source: `{_s['source']}`")
        st.caption("Badalne ke liye ai_config.json edit karein, phir app restart. "
                   "Test: python check_ai_config.py")

    _force_new = st.checkbox("🔄 Naya jawab banao (cache ignore karo — paisa lagega)",
                             value=False, key="admin_force_new")
    _ac = load_agent_cache()
    if _ac:
        st.caption(f"💰 Cache: {len(_ac)} jawab mehfooz — dobara poochne par kharcha Rs 0")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg.get("staff"): st.caption(msg["staff"])
            st.markdown(format_options(msg["content"]))
    ui = st.chat_input("Sawal likhen...") or preset
    if ui:
        st.session_state.messages.append({"role":"user","content":ui})
        with st.chat_message("user"): st.markdown(ui)
        with st.chat_message("assistant"):
            with st.spinner("Staff kaam kar raha hai..."):
                try:
                    sk2, ans, from_cache = handle_request(ui, student, force=_force_new)
                    stitle = STAFF[sk2]["title"]
                    # Only write a new record file for freshly generated answers —
                    # cache hits would otherwise create duplicate Record Room entries.
                    sp = None if from_cache else save_record(STAFF[sk2]["folder"], ui, ans, student)
                except Exception as e:
                    stitle = "⚠️"; ans = f"Error: {e}"; sp = None; from_cache = False
            st.caption(stitle); st.markdown(format_options(ans))
            if from_cache:
                st.caption("♻️ Cache se mila — 0 API call, kharcha Rs 0")
            if sp: st.caption(f"💾 {sp}")
        st.session_state.messages.append({"role":"assistant","content":ans,"staff":stitle})
