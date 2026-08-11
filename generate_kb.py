"""
AI4Kids.pk — Knowledge Base Generator (ALL GRADES)
Generates pre-built lessons + quizzes for Grades 1-5 (all 5 subjects)
Grade 5 already exists — skip if present.
Run once, use forever. Zero API cost after generation.
"""

import json, os, time, sys
import ai_config                      # endpoint config: ai_config.json

client = ai_config.get_client()
MODEL = ai_config.MODEL
KB_DIR = "kb"

# Import topics from main app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# All Grade topics per subject (matching ai4kids_school.py exactly)
ALL_TOPICS = {
    "ai": {
        "teacher": "Ustaad Ji", "name": "AI & Technology",
        1: [("AI kya hai?", "AI kya hota hai? Simple intro"),
            ("Robot dost", "Robots hamare madadgaar"),
            ("Smart vs Silly machine", "Kaunsi machine smart hai?"),
            ("Computer pehchano", "Computer ke hisse — screen, keyboard, mouse"),
            ("Bolta computer", "Alexa, Siri — computer kaise bolta hai?"),
            ("AI games mein", "Video games mein AI kaise khelti hai")],
        2: [("AI ki aankh", "Camera se computer kaise dekhta hai"),
            ("AI ke kaan", "Voice recognition — computer sunti hai"),
            ("Sorting seekho", "Cheezein arrange karna"),
            ("Yes/No decisions", "Computer kaise faisla karti hai"),
            ("AI drawings", "AI se tasveerein banana"),
            ("AI hamare ghar mein", "Washing machine, AC, TV mein AI")],
        3: [("Patterns dhundho", "AI patterns kaise dhundhti hai"),
            ("Data kya hai?", "Data matlab information"),
            ("Algorithm", "Steps ka plan — biryani ki recipe"),
            ("AI aur cricket", "DRS, Hawk-Eye"),
            ("Coding intro", "Computer ko instructions dena"),
            ("AI safe istemal", "Internet safety")],
        4: [("Machine learning", "Computer khud seekhti hai"),
            ("Chatbot kya hai", "ChatGPT, Claude — AI se baat"),
            ("Data types", "Text, numbers, images, audio"),
            ("AI decision tree", "Agar yeh to woh"),
            ("Fake vs real", "Deepfakes pehchano"),
            ("AI jobs", "AI se kaunse kaam hote hain")],
        5: [("Neural network", "Dimaag jaisa computer"),
            ("Prompt engineering", "AI se achi baat kaise karein"),
            ("Computer vision", "AI tasveerein kaise samajhti hai"),
            ("NLP basics", "AI language kaise samajhti hai"),
            ("AI ethics", "AI ka sahi aur ghalat istemal"),
            ("AI project", "Apna chhota AI project design karo")],
    },
    "math": {
        "teacher": "Hisaab Sir", "name": "Hisaab (Math)",
        1: [("Ginti 0-100", "Numbers 0-100 pehchano, likho, gino"),
            ("Jama (+)", "Addition without carrying"),
            ("Minus (-)", "Subtraction without borrowing"),
            ("Pakistani Paisa", "Coins Rs1,2,5,10 aur Notes pehchano"),
            ("Ghadi Parhna", "Analog clock, digital clock, din maheene"),
            ("Ashkaal", "Rectangle, square, circle, triangle")],
        2: [("Numbers 999 tak", "3-digit numbers, place value"),
            ("Jama carrying ke saath", "2/3-digit addition with carrying"),
            ("Minus borrowing ke saath", "2/3-digit subtraction with borrowing"),
            ("Zarb ki tables", "Multiplication tables 2,3,4,5,10"),
            ("Taqseem", "Division within tables"),
            ("Fractions intro", "Half, one-third, quarter")],
        3: [("Roman numbers", "Roman numbers I se XX tak"),
            ("4-digit operations", "Addition/subtraction up to 4-digit"),
            ("Zarb tables 6-9", "Multiplication tables 6,7,8,9"),
            ("Fractions", "Proper, improper, equivalent fractions"),
            ("Naap taul", "Kilometer, meter, cm, kg, gram, liter"),
            ("Data handling", "Carroll diagram, tally chart, picture graph")],
        4: [("Numbers 1 lakh tak", "100,000 tak, place value 6-digit"),
            ("Factors aur multiples", "Prime/composite, divisibility rules"),
            ("Fractions operations", "Like/unlike, multiply, divide fractions"),
            ("Decimals", "Decimal place value, fraction to decimal"),
            ("Naap conversions", "km-m, kg-g, L-mL, 24-hour time"),
            ("Geometry angles", "Protractor, acute/obtuse/right angles")],
        5: [("Numbers 10 lakh tak", "1,000,000 tak, multiply/divide by 10,100,1000"),
            ("HCF aur LCM", "Prime factorization se HCF/LCM"),
            ("Decimals aur percentage", "3-decimal places, percentage"),
            ("Fractions advanced", "Different denominators, multiply/divide"),
            ("Geometry shapes", "Triangles, quadrilaterals, symmetry"),
            ("Perimeter aur area", "Square/rectangle formulas")],
    },
    "english": {
        "teacher": "English Ma'am", "name": "English",
        1: [("Alphabets aur Phonics", "A-Z upper/lower case, letter sounds"),
            ("Sight words", "High-frequency words — the, is, am, are"),
            ("Mera ghar meri family", "My family, body parts — simple sentences"),
            ("Animals aur colors", "Animals, colors, numbers vocabulary"),
            ("Story time", "Short stories with pictures"),
            ("Writing practice", "Letters aur words trace karo")],
        2: [("Paragraphs parhna", "Short paragraphs aur stories reading"),
            ("Nouns aur verbs", "Grammar — nouns aur verbs"),
            ("School aur ghar", "Vocabulary — school, home, food, clothes"),
            ("Sentences banana", "Statements aur questions likhna"),
            ("Listening skills", "2-3 step instructions follow karna"),
            ("Picture describe karo", "Tasveeron ke baare mein batao")],
        3: [("Stories aur poems", "Reading fiction, poetry, comprehension"),
            ("Grammar: Nouns types", "Common/proper nouns, pronouns, adjectives"),
            ("Tenses intro", "Simple present aur past tense"),
            ("Punctuation", "Full stop, question mark, comma"),
            ("Paragraph likhna", "5-6 sentences ka paragraph"),
            ("Letter writing", "Informal letter — dost ko khat")],
        4: [("Fiction aur non-fiction", "Stories, articles, poetry — inference"),
            ("Grammar advanced", "Adverbs, prepositions, conjunctions"),
            ("Tenses: Present Past Future", "Simple aur continuous tenses"),
            ("Vocabulary building", "Prefixes, suffixes, compound words"),
            ("Essay aur diary", "Short essays, diary entries"),
            ("Formal letter", "Formal aur informal letter writing")],
        5: [("Comprehension skills", "Summarize, predict, infer"),
            ("Active/Passive voice", "Active ko passive mein badalna"),
            ("All tenses review", "Past, present, future — all forms"),
            ("Idioms aur proverbs", "Muhavare aur kahawatein"),
            ("Essay aur story writing", "Essays, stories, book reviews"),
            ("Creative writing", "Poetry, dialogue, application letter")],
    },
    "science": {
        "teacher": "Science Sir", "name": "General Science",
        1: [("Mera jism", "Jism ke hisse aur unke kaam"),
            ("Paanch hasiyaat", "5 senses — dekhna, sunna, chhoona"),
            ("Janwar", "Ghar ke aur junglee janwar"),
            ("Podhe", "Podhe ke hisse — jar, tana, patti, phool"),
            ("Sehat aur safai", "Healthy khana, haath dhona"),
            ("Mausam", "Dhoop, baarish, badal, hawa")],
        2: [("Zinda aur be-jaan", "Living aur non-living cheezein"),
            ("Janwar ki qismein", "Zameen, paani, hawa ke janwar"),
            ("Podha kaise ugta hai", "Beej se podha — seed to plant"),
            ("Khana ki qismein", "Energy, body-building, protective food"),
            ("Paani ki ahmiyat", "Paani ke uses, paani bachao"),
            ("Pakistan ke seasons", "Garmi, sardi, barsat, bahar")],
        3: [("Haddiyaan aur muscles", "Human body — bones, muscles, teeth"),
            ("Sehatmand aadat", "Exercise, neend, balanced diet"),
            ("Matter: solid liquid gas", "Thos, maaye, gas"),
            ("Paani ka safar", "Water cycle — evaporation, condensation"),
            ("Din aur raat", "Zameen ghumti hai — din kyun aata hai"),
            ("Community helpers", "Doctor, teacher, farmer, police")],
        4: [("Hazam ka nizam", "Digestive system"),
            ("Taqat aur harkat", "Force and motion — push, pull, friction"),
            ("Simple machines", "Lever, pulley, wheel"),
            ("Roshni aur saya", "Light sources, shadows, reflection"),
            ("Awaaz", "Sound sources, loud/soft, high/low"),
            ("Solar system", "Suraj, zameen, chaand, sitare")],
        5: [("Khoon ka nizam", "Circulatory system — dil, khoon"),
            ("Cells", "Cell — jism ki chhoti eent"),
            ("Bijli ke circuits", "Electricity — circuits, conductors"),
            ("Magnet ki taqat", "Magnetism — poles, attraction"),
            ("Ecosystem", "Margalla Hills ecosystem, food web"),
            ("Technology aur safety", "Computers, internet safety")],
    },
    "robotics": {
        "teacher": "Robotics Ustaad", "name": "Automation & Robotics",
        1: [("Machine kya hai?", "Simple machines — lever, wheel"),
            ("Robot kya karta?", "Robots kya kar sakte hain"),
            ("Sensor dost", "Sensors — robot ki aankhein aur kaan"),
            ("Motor chalo!", "Motor kaise ghoomta hai"),
            ("Traffic light", "Traffic signal kaise kaam karta hai"),
            ("Toy robot", "Apna toy robot design karo")],
        2: [("Ghar ki machines", "Washing machine, mixer, iron"),
            ("Remote control", "Remote kaise kaam karta hai"),
            ("Battery aur switch", "Battery se bijli, switch se control"),
            ("Gears aur pulleys", "Gears se taqat badhao"),
            ("Robot ke hisse", "Motor, sensor, body, brain"),
            ("Paper robot banao", "Kagaz ka robot design karo")],
        3: [("Simple circuits", "Battery, wire, bulb — circuit banao"),
            ("Automatic machines", "Washing machine kaise sochti hai"),
            ("Robot ki aankhein", "Sensors — touch, light, sound"),
            ("Wheels vs legs", "Robot movement types"),
            ("Factory mein machines", "Assembly line kya hai"),
            ("Block robots", "LEGO/blocks se robot banao")],
        4: [("Arduino intro", "Arduino — chhota computer"),
            ("Drone udaan", "Drone kaise udta hai"),
            ("Factory robot", "Factory mein robot"),
            ("Line follower", "Line follow karne wala robot"),
            ("Automatic gate", "Automatic darwaza"),
            ("Robotic arm", "Haath jaisa robot")],
        5: [("IoT basics", "Internet of Things — smart devices"),
            ("3D printing", "3D printer se cheezein banana"),
            ("AI + Robotics", "Jab AI robot mein aaye"),
            ("Self-driving car", "Khud chalti gaari ka system"),
            ("Space robots", "Space mein robots — Mars rovers"),
            ("Future tech", "Pakistan mein automation ka mustaqbil")],
    },
}

LESSON_PROMPT = """Tum AI4Kids.pk ke {teacher} ho. Grade {grade} ke bachon ko {subject} padhate ho.
ROMAN URDU ONLY mein likho. Pakistani examples use karo. Bachay ka naam student hai.

Ek complete lesson likho is topic par: "{title}" — {desc}

FORMAT:
## HOOK
(2-3 lines dilchasp sawaal ya kahani — Pakistani context)

## SAMJHAO
(4-5 chhote paragraphs mein concept samjhao — simple Roman Urdu)

## MISAAL
(Ek Pakistani real-life example — bazaar, cricket, rickshaw, biryani)

## KARO
(Hands-on activity jo ghar ya school mein kar sakein)

## SAWAAL
(3 review questions)

Roman Urdu mein. Technical terms English mein rakh sakte ho. Sign off as {teacher}."""

QUIZ_PROMPT = """Tum AI4Kids.pk ke Examiner Sahib ho. Grade {grade} ka quiz banao.
ROMAN URDU ONLY. Pakistani examples. Topic: "{title}" — {desc}. Subject: {subject}.

ONLY valid JSON, no other text:
{{"title":"{title} Quiz","questions":[
{{"q":"Sawaal?","a":"Option A","b":"Option B","c":"Option C","d":"Option D","correct":"a","explanation":"Kyun sahi hai"}},
{{"q":"...","a":"...","b":"...","c":"...","d":"...","correct":"b","explanation":"..."}},
{{"q":"...","a":"...","b":"...","c":"...","d":"...","correct":"c","explanation":"..."}},
{{"q":"...","a":"...","b":"...","c":"...","d":"...","correct":"a","explanation":"..."}},
{{"q":"...","a":"...","b":"...","c":"...","d":"...","correct":"d","explanation":"..."}}
]}}
5 MCQ. Roman Urdu. correct = "a","b","c","d"."""


def generate(grade):
    grade_dir = os.path.join(KB_DIR, f"grade_{grade}")
    os.makedirs(grade_dir, exist_ok=True)

    total_topics = sum(len(s[grade]) for s in ALL_TOPICS.values())
    done = 0

    for subj_key, subj in ALL_TOPICS.items():
        filepath = os.path.join(grade_dir, f"{subj_key}.json")
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            if size > 5000:
                print(f"  SKIP {subj_key}.json (already exists, {size} bytes)")
                done += len(subj[grade])
                continue

        print(f"\n  Subject: {subj['name']} ({subj['teacher']})")
        subject_data = {"subject": subj_key, "name": subj["name"],
                        "teacher": subj["teacher"], "grade": grade, "topics": []}

        for title, desc in subj[grade]:
            done += 1
            print(f"    [{done}/{total_topics}] {title}...", end=" ")

            # Lesson
            try:
                r = client.chat.completions.create(model=MODEL, max_tokens=2000,
                    messages=[{"role":"user","content": LESSON_PROMPT.format(
                        teacher=subj["teacher"], grade=grade, subject=subj["name"],
                        title=title, desc=desc)}])
                lesson = r.choices[0].message.content.strip()
            except Exception as e:
                lesson = f"Error generating: {e}"
            print("lesson OK", end=" ")

            # Quiz
            try:
                r = client.chat.completions.create(model=MODEL, max_tokens=1500,
                    messages=[{"role":"user","content": QUIZ_PROMPT.format(
                        grade=grade, title=title, desc=desc, subject=subj["name"])}])
                qt = r.choices[0].message.content.strip()
                qt = qt.replace("```json","").replace("```","").strip()
                quiz = json.loads(qt[qt.find("{"):qt.rfind("}")+1])
            except Exception as e:
                print(f"quiz ERROR ({e})", end=" ")
                quiz = {"title": title, "questions": []}
            print("quiz OK")

            subject_data["topics"].append({"title": title, "description": desc,
                                           "lesson": lesson, "quiz": quiz})
            time.sleep(0.5)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(subject_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {filepath}")


def main():
    grades = [int(g) for g in sys.argv[1:]] if len(sys.argv) > 1 else [1, 2, 3, 4, 5]
    for g in grades:
        print(f"\n{'='*60}")
        print(f"GRADE {g}")
        print(f"{'='*60}")
        generate(g)
    print(f"\n{'='*60}")
    print("ALL DONE!")
    for g in grades:
        gd = os.path.join(KB_DIR, f"grade_{g}")
        files = os.listdir(gd) if os.path.isdir(gd) else []
        print(f"  Grade {g}: {len(files)} files")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
