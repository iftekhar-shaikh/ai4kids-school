# AI4Kids.pk — Khan Academy Model Implementation Guide
# Reference for building the complete virtual school experience
# Based on research: proven learning gains, gamification, supervised implementation

# =====================================================================
# WHAT'S ALREADY BUILT ✅
# =====================================================================

ALREADY_DONE = {
    "structured_daily_workflow": "Assembly → Timetable → Hallway → Classroom → Quiz → Stars",
    "gamification_stars_badges": "Stars per activity, streak fire, leaderboard, levels (Pilot→Astronaut)",
    "interactive_quizzes": "MCQ with A/B/C/D buttons, auto-marking, instant feedback",
    "bite_sized_lessons": "5-step format: Hook → Samjhao → Misaal → Karo → Quiz",
    "teacher_personas": "Ustaad Ji, Hisaab Sir, English Ma'am, Science Sir, Robotics Ustaad, Examiner Sahib",
    "community_feel": "Assembly greeting, section identity, school bell, word of the day",
    "bilingual_delivery": "Roman Urdu + English technical terms",
    "knowledge_base": "Pre-built Grade 5 lessons (30 topics, 150 MCQs) — zero API cost",
    "immediate_feedback": "Quiz results with ✅/❌ per question + explanations",
    "decorated_classrooms": "5 themed rooms with wall items, blackboard, desk, window views",
}

# =====================================================================
# WHAT TO BUILD NEXT (Priority Order)
# =====================================================================

PRIORITY_1_QUICK_WINS = {
    "movement_breaks": {
        "description": "Dance break / stretch between periods",
        "implementation": "After every 2 lessons, show 'Break ka waqt!' screen with fun activity",
        "effort": "Small — just a new screen in student mode",
    },
    "celebration_screen": {
        "description": "Achievement celebrations when milestones hit",
        "implementation": "Special screen with confetti when student hits 10/25/50 stars or completes a subject",
        "effort": "Small — trigger on star thresholds",
    },
    "daily_progress_summary": {
        "description": "End-of-day summary: what you learned today",
        "implementation": "Chhuti screen showing: lessons done, quizzes taken, stars earned, streak status",
        "effort": "Small — count session activities",
    },
}

PRIORITY_2_MEDIUM_EFFORT = {
    "printable_worksheets": {
        "description": "Downloadable PDF worksheets per topic for offline practice",
        "implementation": "Generate worksheet from KB lesson → PDF with fill-in-blanks, match pairs, drawing",
        "effort": "Medium — need PDF generation skill",
        "khan_insight": "Critical for kids with limited internet",
    },
    "adaptive_learning_path": {
        "description": "Track what student has completed, suggest next topic",
        "implementation": "Save completed_topics in students.json, show ✅/🔒 on topic buttons",
        "effort": "Medium — need progress tracking per topic per student",
        "khan_insight": "Let advanced students move ahead, slower ones get reinforcement",
    },
    "parent_daily_report": {
        "description": "Auto-generated report for parents: what child did today",
        "implementation": "Admin Office generates summary from session log, copyable for WhatsApp",
        "effort": "Medium — need session logging + report generation",
        "khan_insight": "Supervised implementation = 6x more usage",
    },
    "video_links": {
        "description": "Link to relevant YouTube/Khan Academy videos per topic",
        "implementation": "Add video_url field to KB topics, show 'Watch video' button in lesson",
        "effort": "Small — but need to curate video links manually",
        "khan_insight": "Flipped classroom: video at home, practice at school",
    },
}

PRIORITY_3_BIG_FEATURES = {
    "peer_collaboration": {
        "description": "Buddy system — pair students for activities",
        "implementation": "Show classmate's progress, shared challenges, peer quiz battles",
        "effort": "Large — need multi-user sessions",
        "khan_insight": "Improves engagement by 25%",
    },
    "adaptive_difficulty": {
        "description": "Auto-adjust quiz difficulty based on performance",
        "implementation": "If student gets 5/5, next quiz is harder. If 2/5, give easier review quiz",
        "effort": "Large — need difficulty tagging + adaptive logic",
        "khan_insight": "Mastery-based progression reduces fear of failure",
    },
    "offline_mode": {
        "description": "Full app works without internet (KB lessons only)",
        "implementation": "Detect offline, disable API features, show KB content only",
        "effort": "Medium — KB already works offline, just need graceful fallback",
    },
    "themed_challenges": {
        "description": "Weekly treasure hunts, themed quiz battles, special events",
        "implementation": "Time-limited challenges: 'Pakistan Day Science Quiz', 'Eid Math Challenge'",
        "effort": "Medium — need event system + special content",
    },
}

# =====================================================================
# IMPLEMENTATION ROADMAP
# =====================================================================

ROADMAP = """
Phase 1 (This week): Quick wins
  → Movement breaks between periods
  → Celebration screens for milestones
  → Daily progress summary (Chhuti screen)

Phase 2 (Next week): Student tracking
  → Adaptive learning path (completed topics tracking)
  → Parent daily report generator
  → Video links in lessons

Phase 3 (Week 3): Offline + Print
  → Printable worksheets (PDF)
  → Offline mode with KB
  → Expand KB to Grades 1-4

Phase 4 (Month 2): Advanced
  → Adaptive difficulty quizzes
  → Peer collaboration / buddy system
  → Themed weekly challenges
  → Deploy to Streamlit Cloud
"""
