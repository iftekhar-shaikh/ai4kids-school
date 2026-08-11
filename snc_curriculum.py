# ========================================================================
# PAKISTAN SINGLE NATIONAL CURRICULUM (SNC) — CLASS 1 TO 5
# Reference for AI4Kids.pk Course Alignment
# Source: Ministry of Federal Education & Professional Training, Pakistan
# ========================================================================

# -----------------------------------------------------------------------
# SUBJECTS STRUCTURE (SNC)
# -----------------------------------------------------------------------
# Class 1-3: Urdu, English, Mathematics, General Knowledge, Islamiat
# Class 4-5: Urdu, English, Mathematics, General Science, Social Studies, Islamiat
#
# AI4Kids.pk maps to these SNC subjects:
#   Math      → SNC Mathematics
#   English   → SNC English
#   Science   → SNC General Knowledge (1-3) + General Science (4-5)
#   AI        → Extra-curricular (technology literacy)
#   Robotics  → Extra-curricular (STEM)

# ========================================================================
# MATHEMATICS — SNC Grade I-V
# 4 Strands: Numbers & Operations, Algebra, Geometry & Measurement, Data
# ========================================================================

MATH_CURRICULUM = {
    1: {
        "title": "Mathematics Grade I",
        "units": [
            {
                "unit": "Whole Numbers",
                "topics": [
                    "Numbers 0-9: identify, read, write, count, match",
                    "Numbers up to 100: read, write, count forward/backward",
                    "Place value: tens and ones",
                    "Compare and order numbers 0-99",
                    "Ordinal numbers: 1st to 10th",
                    "Missing numbers in sequence 1-100",
                ]
            },
            {
                "unit": "Number Operations",
                "topics": [
                    "Addition without carrying (1-digit + 1-digit, 2-digit + 2-digit)",
                    "Addition symbol + and = ",
                    "Subtraction without borrowing (up to 2-digit)",
                    "Subtraction symbol -",
                    "Mental math: add/subtract up to 20",
                    "Number stories with pictures",
                ]
            },
            {
                "unit": "Measurement: Length and Mass",
                "topics": [
                    "Compare heights/lengths: long/short, tall/short",
                    "Compare mass: heavy/light",
                ]
            },
            {
                "unit": "Money (Pakistani Currency)",
                "topics": [
                    "Identify coins: Rs 1, 2, 5, 10",
                    "Identify notes: Rs 10, 20, 50, 100",
                    "Match equivalent denominations",
                    "Add/subtract money (up to Rs 100)",
                    "Make purchases and give change",
                ]
            },
            {
                "unit": "Time",
                "topics": [
                    "Hour and minute hands on analog clock",
                    "Tell time in hours (2 o'clock)",
                    "Digital clock reading",
                    "Days of the week (order, before/after)",
                    "Solar months of the year",
                    "Islamic months of the year",
                ]
            },
            {
                "unit": "Geometry",
                "topics": [
                    "Basic shapes: rectangle, square, circle, triangle",
                    "Match shapes in daily life",
                    "Classify by sides and corners",
                    "Patterns: identify and extend (2-3 elements)",
                    "Position: inside/outside, above/below, near/far",
                ]
            },
        ],
        "weightage": {"Whole Numbers": 39, "Operations": 25, "Measurement": 6, "Money": 8, "Time": 10, "Geometry": 12},
    },
    2: {
        "title": "Mathematics Grade II",
        "units": [
            {
                "unit": "Whole Numbers",
                "topics": [
                    "Ordinal numbers: 1st to 20th",
                    "Numbers 1-100 in words",
                    "Read/write numbers up to 999",
                    "Place value: hundreds, tens, ones",
                    "Compare 2-digit and 3-digit numbers",
                    "Count in 10s and 100s",
                    "Ascending/descending order up to 999",
                ]
            },
            {
                "unit": "Number Operations",
                "topics": [
                    "Addition with carrying (2-digit, 3-digit)",
                    "Subtraction with borrowing (2-digit, 3-digit)",
                    "Mental math up to 50",
                    "Multiplication as repeated addition",
                    "Multiplication tables: 2, 3, 4, 5, 10",
                    "Division symbol and concept",
                    "Division within multiplication tables",
                    "Mixed operations word problems",
                ]
            },
            {
                "unit": "Fractions",
                "topics": [
                    "Fraction as equal parts of whole",
                    "Half (1/2), one-third (1/3), quarter (1/4)",
                    "Unit fractions up to 1/10",
                    "Shade fractions in figures",
                ]
            },
            {
                "unit": "Measurement",
                "topics": [
                    "Length: meter and centimeter",
                    "Mass: kilogram and gram",
                    "Capacity: liter and milliliter",
                    "Add/subtract within 100 (same units)",
                ]
            },
            {
                "unit": "Time",
                "topics": [
                    "Hours in a day, minutes in an hour",
                    "Read time with 5-minute intervals",
                    "a.m. and p.m.",
                    "Draw clock hands",
                    "Solar and Islamic calendar",
                ]
            },
            {
                "unit": "Geometry",
                "topics": [
                    "Shapes: square, rectangle, triangle, circle, semi-circle",
                    "Vertices and sides",
                    "Straight lines vs curves",
                    "Draw straight line with ruler",
                    "Patterns on square grid",
                    "3-D objects: cube, cuboid, cylinder, cone, sphere",
                ]
            },
        ],
        "weightage": {"Whole Numbers": 18, "Operations": 44, "Fractions": 7, "Measurement": 14, "Time": 8, "Geometry": 9},
    },
    3: {
        "title": "Mathematics Grade III",
        "units": [
            {
                "unit": "Whole Numbers",
                "topics": [
                    "Roman numbers up to 20 (read and write)",
                    "Even and odd numbers up to 99",
                    "Numbers up to 10,000 in numerals and words",
                    "Place value up to 5-digit",
                    "Number line up to 2-digit",
                    "Compare using <, >, = (up to 3-digit)",
                    "Rounding to nearest 10 and 100",
                ]
            },
            {
                "unit": "Number Operations",
                "topics": [
                    "Addition up to 4-digit with/without carrying",
                    "Subtraction up to 4-digit with/without borrowing",
                    "Mental math up to 100",
                    "Multiplication tables: 6, 7, 8, 9",
                    "Multiply 2-digit by 1-digit",
                    "Multiply by 0 and 1",
                    "Division: 2-digit by 1-digit (zero remainder)",
                    "Real life word problems",
                ]
            },
            {
                "unit": "Fractions",
                "topics": [
                    "Express fractions in figures and vice versa",
                    "Proper and improper fractions",
                    "Equivalent fractions",
                    "Compare fractions (same denominator)",
                    "Add/subtract fractions (same denominator)",
                ]
            },
            {
                "unit": "Measurement",
                "topics": [
                    "Length: kilometer, meter, centimeter",
                    "Mass: kilogram, gram",
                    "Capacity: liter, milliliter",
                    "Add/subtract in same units (no carrying)",
                    "Perimeter of square, rectangle, triangle",
                ]
            },
            {
                "unit": "Time",
                "topics": [
                    "a.m. and p.m. with 12-hour clock",
                    "Read analog and digital clocks",
                    "Calendar: days and dates",
                    "Add/subtract time in hours",
                ]
            },
            {
                "unit": "Geometry",
                "topics": [
                    "Point, line, ray, line segment",
                    "Quadrilaterals and triangles",
                    "Circle: center, radius, diameter",
                    "Line symmetry",
                    "3-D: cubes, cuboids, pyramids (edges/faces)",
                    "Measure line segments (cm and mm)",
                ]
            },
            {
                "unit": "Data Handling",
                "topics": [
                    "Carroll diagram",
                    "Tally charts",
                    "Picture graphs (read and interpret)",
                ]
            },
        ],
        "weightage": {"Whole Numbers": 16, "Operations": 20, "Fractions": 16, "Measurement": 21, "Time": 10, "Geometry": 13, "Data": 4},
    },
    4: {
        "title": "Mathematics Grade IV",
        "units": [
            {
                "unit": "Whole Numbers and Operations",
                "topics": [
                    "Numbers up to 100,000 (read, write, compare)",
                    "Place value up to 6-digit",
                    "Addition up to 5-digit",
                    "Subtraction up to 5-digit",
                    "Multiplication up to 4-digit by 2-digit",
                    "Division up to 4-digit by 2-digit",
                    "Number patterns (increasing/decreasing)",
                ]
            },
            {
                "unit": "Factors and Multiples",
                "topics": [
                    "Divisibility rules for 2, 3, 5, 10",
                    "Prime and composite numbers up to 100",
                    "Factors of numbers up to 50",
                    "First ten multiples",
                    "Prime factorization",
                    "Common factors and common multiples",
                ]
            },
            {
                "unit": "Fractions",
                "topics": [
                    "Like and unlike fractions",
                    "Simplify to lowest form",
                    "Proper, improper, mixed numbers",
                    "Convert improper to mixed and vice versa",
                    "Add/subtract like fractions",
                    "Multiply fractions by whole numbers",
                    "Multiply proper/improper/mixed fractions",
                    "Divide fraction by whole number",
                ]
            },
            {
                "unit": "Decimals",
                "topics": [
                    "Decimal as alternative to fraction",
                    "Place value up to 3 decimal places",
                    "Convert fraction to decimal and vice versa",
                    "Add/subtract up to 2 decimal places",
                    "Multiply by 10, 100, 1000",
                    "Multiply/divide 2-digit with 1 decimal place",
                    "Rounding: whole numbers to 10/100/1000",
                    "Rounding decimals to nearest whole number",
                ]
            },
            {
                "unit": "Measurement",
                "topics": [
                    "Convert: km-m, m-cm, cm-mm, kg-g, g-mg, L-mL",
                    "Add/subtract measures in same units",
                    "Time: 12-hour and 24-hour format",
                    "Convert: hours-minutes, minutes-seconds",
                    "Convert: years-months, months-days, weeks-days",
                ]
            },
            {
                "unit": "Geometry",
                "topics": [
                    "Parallel and non-parallel lines",
                    "Angles: measure with protractor",
                    "Acute, obtuse, right angles",
                    "Circle: radius, diameter, circumference",
                    "Perimeter and area on square grid",
                    "Line symmetry on grid/dot pattern",
                    "3-D objects: compare and sort",
                ]
            },
            {
                "unit": "Data Handling",
                "topics": [
                    "Bar graphs (horizontal and vertical)",
                    "Line graphs",
                    "Pie charts",
                    "Interpret real life data",
                ]
            },
        ],
        "weightage": {"Numbers+Operations": 17, "Factors": 11, "Fractions": 15, "Decimals": 15, "Measurement": 19, "Geometry": 16, "Data": 7},
    },
    5: {
        "title": "Mathematics Grade V",
        "units": [
            {
                "unit": "Whole Numbers and Operations",
                "topics": [
                    "Numbers up to 1,000,000 (one million)",
                    "Add/subtract up to 6-digit",
                    "Multiply up to 5-digit by 10/100/1000",
                    "Multiply up to 5-digit by 3-digit",
                    "Divide up to 5-digit by 10/100/1000",
                    "Divide up to 5-digit by 2-digit",
                    "Number patterns: identify rule, extend",
                ]
            },
            {
                "unit": "HCF and LCM",
                "topics": [
                    "HCF of 2 or 3 numbers (prime factorization + division)",
                    "LCM of 2 or 3 numbers (prime factorization + division)",
                    "Real life situations involving HCF and LCM",
                ]
            },
            {
                "unit": "Fractions",
                "topics": [
                    "Add/subtract fractions with different denominators",
                    "Multiply fraction by 1-digit (with diagram)",
                    "Multiply proper/improper/mixed fractions",
                    "Divide fraction by fraction",
                    "Real life fraction problems",
                ]
            },
            {
                "unit": "Decimals and Percentages",
                "topics": [
                    "Compare/arrange decimals up to 2 places",
                    "Add/subtract up to 3 decimal places",
                    "Multiply/divide decimals by 10/100/1000",
                    "Multiply decimals by whole numbers",
                    "Multiply/divide decimals by decimals",
                    "Convert fractions to decimals using division",
                    "Percentage as special fraction",
                    "Convert: percentage to fraction to decimal",
                    "Real life percentage problems",
                ]
            },
            {
                "unit": "Distance and Time",
                "topics": [
                    "Convert: km-m, m-cm, cm-mm (both ways)",
                    "Convert: hours-minutes-seconds (both ways)",
                    "Convert: years-months-days-weeks (both ways)",
                    "Add/subtract time with carrying/borrowing",
                    "Real life distance and time problems",
                ]
            },
            {
                "unit": "Unitary Method",
                "topics": [
                    "Value of one from value of many",
                    "Value of many from value of one",
                    "Value of many from value of some",
                ]
            },
            {
                "unit": "Geometry",
                "topics": [
                    "Angles: acute, right, obtuse, straight, reflex",
                    "Adjacent, complementary, supplementary angles",
                    "Triangles: equilateral, isosceles, scalene",
                    "Triangles: acute, obtuse, right-angled",
                    "Construct triangle (protractor + ruler)",
                    "Quadrilaterals: square, rectangle, parallelogram, rhombus, trapezium, kite",
                    "Construct square and rectangle",
                    "Symmetry: reflective and rotational",
                    "3-D nets: cubes, cuboids, pyramids",
                ]
            },
            {
                "unit": "Perimeter and Area",
                "topics": [
                    "Differentiate perimeter and area",
                    "Formulas for square and rectangle",
                    "Real life perimeter and area problems",
                ]
            },
            {
                "unit": "Data Handling",
                "topics": [
                    "Average of given data",
                    "Organize data in bar graphs",
                    "Read/interpret horizontal and vertical bar graphs",
                    "Real life data problems",
                ]
            },
        ],
        "weightage": {"Numbers+Operations": 14, "HCF_LCM": 5, "Fractions": 8, "Decimals+Percent": 25, "Distance+Time": 9, "Unitary": 4, "Geometry": 20, "Perimeter+Area": 6, "Data": 9},
    },
}

# ========================================================================
# ENGLISH — SNC Grade I-V (Key Areas)
# ========================================================================

ENGLISH_CURRICULUM = {
    1: {
        "title": "English Grade I",
        "areas": [
            "Alphabet recognition (upper and lower case)",
            "Phonics: letter sounds, blending",
            "Sight words and high-frequency words",
            "Simple sentences (subject + verb)",
            "Reading: short stories with pictures",
            "Vocabulary: family, body parts, animals, colors, numbers",
            "Listening and speaking: greetings, instructions",
            "Writing: trace and copy letters, words",
        ]
    },
    2: {
        "title": "English Grade II",
        "areas": [
            "Reading: short paragraphs, stories",
            "Phonics: digraphs, blends",
            "Grammar: nouns, verbs (action words)",
            "Sentence types: statements, questions",
            "Vocabulary: school, home, food, clothes, weather",
            "Writing: simple sentences, fill in blanks",
            "Listening: follow 2-3 step instructions",
            "Speaking: describe pictures, tell stories",
        ]
    },
    3: {
        "title": "English Grade III",
        "areas": [
            "Reading: stories, poems, information texts",
            "Comprehension: answer questions from text",
            "Grammar: nouns (common/proper), pronouns, adjectives",
            "Tenses: simple present and past",
            "Punctuation: full stop, question mark, comma",
            "Vocabulary: synonyms, antonyms",
            "Writing: short paragraphs (5-6 sentences)",
            "Letter writing: informal",
            "Speaking: narrate events, describe people",
        ]
    },
    4: {
        "title": "English Grade IV",
        "areas": [
            "Reading: fiction, non-fiction, poetry",
            "Comprehension: inference, main idea",
            "Grammar: adverbs, prepositions, conjunctions",
            "Tenses: present, past, future (simple and continuous)",
            "Punctuation: apostrophe, quotation marks",
            "Vocabulary: prefixes, suffixes, compound words",
            "Writing: paragraphs, short essays, diary entries",
            "Letter writing: formal and informal",
            "Speaking: debates, presentations",
        ]
    },
    5: {
        "title": "English Grade V",
        "areas": [
            "Reading: longer texts, articles, stories",
            "Comprehension: summarize, predict, infer",
            "Grammar: active/passive voice, direct/indirect speech",
            "Tenses: all tenses review",
            "Vocabulary: idioms, proverbs, context clues",
            "Writing: essays, stories, book reviews",
            "Letter writing: application, complaint",
            "Creative writing: poetry, dialogue",
            "Speaking: group discussions, role play",
        ]
    },
}

# ========================================================================
# GENERAL KNOWLEDGE (Class 1-3) / GENERAL SCIENCE (Class 4-5)
# ========================================================================

SCIENCE_CURRICULUM = {
    1: {
        "title": "General Knowledge Grade I",
        "areas": [
            "My body: parts and their functions",
            "Five senses: see, hear, smell, taste, touch",
            "My family and home",
            "Animals: domestic and wild",
            "Plants: parts of a plant",
            "Food: healthy and unhealthy",
            "Cleanliness and hygiene",
            "Weather: sunny, rainy, cloudy, windy",
            "Pakistan: our country, flag, national anthem",
        ]
    },
    2: {
        "title": "General Knowledge Grade II",
        "areas": [
            "Living and non-living things",
            "Animals: land, water, air animals",
            "Plants: how they grow (seed to plant)",
            "Food groups: energy, body-building, protective",
            "Water: uses, saving water",
            "Air: importance, pollution",
            "Seasons of Pakistan",
            "Our neighborhood: school, masjid, hospital",
            "Transport: land, water, air",
            "Pakistan: provinces, capital, famous places",
        ]
    },
    3: {
        "title": "General Knowledge Grade III",
        "areas": [
            "Human body: bones, muscles, teeth",
            "Healthy habits: exercise, sleep, balanced diet",
            "Animals: habitats, food chains",
            "Plants: types (herbs, shrubs, trees), photosynthesis intro",
            "Matter: solids, liquids, gases",
            "Water cycle: evaporation, condensation, rain",
            "Earth: rotation, day and night",
            "Maps and directions",
            "Community helpers: doctor, teacher, farmer, police",
            "Pakistan: national symbols, heroes",
        ]
    },
    4: {
        "title": "General Science Grade IV",
        "areas": [
            "Human body: digestive system, respiratory system",
            "Food and nutrition: vitamins, minerals",
            "Plants: reproduction, seed dispersal",
            "Animals: vertebrates and invertebrates",
            "Matter: properties, changes (reversible/irreversible)",
            "Force and motion: push, pull, friction",
            "Simple machines: lever, pulley, wheel",
            "Light: sources, shadows, reflection",
            "Sound: sources, loud/soft, high/low",
            "Earth: layers, rocks, soil",
            "Solar system: sun, planets",
            "Environment: pollution, conservation",
        ]
    },
    5: {
        "title": "General Science Grade V",
        "areas": [
            "Human body: circulatory system, nervous system",
            "Health: diseases, vaccination, first aid",
            "Plants: photosynthesis, respiration",
            "Animals: life cycles, adaptation",
            "Cells: basic unit of life",
            "Matter: atoms, molecules, elements intro",
            "Energy: forms (heat, light, sound, electrical)",
            "Electricity: circuits, conductors, insulators",
            "Magnetism: poles, attraction, repulsion",
            "Force: gravity, types of forces",
            "Earth: earthquakes, volcanoes, erosion",
            "Solar system: moon, stars, eclipses",
            "Environment: ecosystems, food web, conservation",
            "Technology: computers, internet safety",
        ]
    },
}

# ========================================================================
# AI4KIDS.PK SUBJECT MAPPING
# ========================================================================
# Our 5 subjects mapped to SNC:
#
# 1. MATH        → Direct alignment with SNC Math curriculum above
# 2. ENGLISH     → Direct alignment with SNC English curriculum above
# 3. SCIENCE     → Direct alignment with SNC GK (1-3) + Science (4-5)
# 4. AI          → Extra: Technology literacy (not in SNC, our USP)
# 5. ROBOTICS    → Extra: STEM hands-on (not in SNC, our USP)
#
# NEXT STEPS:
# - Update topic buttons in each classroom to match SNC units
# - Grade-match the topics exactly (not just grade bands)
# - Ensure teachers generate content aligned to SNC SLOs
# - Add SNC unit names in the timetable/classroom headers
# ========================================================================
