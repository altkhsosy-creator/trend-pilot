# ملف إعدادات الموسيقى الخلفية لمشروع Trend Pilot
# يحدد أي موسيقى سيتم تشغيلها حسب نوع القصة

MUSIC_MAPPING = {
    "mystery": "bgm_mystery.mp3",
    "inspiring": "bgm_inspiring.mp3", 
    "horror": "bgm_horror.mp3",
    "crime": "bgm_crime.mp3",
    "suspense": "bgm_suspense.mp3",
    "reflective": "bgm_reflective.mp3",
    "investigative": "bgm_investigative.mp3",
    "default": "bgm_calm.mp3"
}

def get_music_for_story(story_type: str) -> str:
    """إرجاع اسم ملف الموسيقى المناسب لنوع القصة"""
    return MUSIC_MAPPING.get(story_type, MUSIC_MAPPING["default"])
