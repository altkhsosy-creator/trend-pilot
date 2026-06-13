# نظام الموسيقى الديناميكي - يغير الموسيقى حسب نوع المقطع

SEGMENT_MUSIC = {
    "hook_start": "bgm_suspense.mp3",      # بداية hook - تشويق سريع
    "hook_middle": "bgm_investigative.mp3", # وسط hook - تصاعد
    "hook_end": "bgm_horror.mp3",          # نهاية hook - صدمة/رعب
    
    "story_normal": "bgm_calm.mp3",         # سرد عادي - موسيقى هادئة
    "story_tension": "bgm_suspense.mp3",    # لحظات توتر - تشويق
    "story_climax": "bgm_final_boss.mp3",   # الذروة - موسيقى قوية
    
    "emotional": "bgm_reflective.mp3",      # لحظات عاطفية
    "closing": "bgm_mystery.mp3"           # خاتمة - غموض
}

def get_music_for_segment(segment_type: str) -> str:
    """إرجاع اسم ملف الموسيقى المناسب لنوع المقطع"""
    return SEGMENT_MUSIC.get(segment_type, "bgm_calm.mp3")
