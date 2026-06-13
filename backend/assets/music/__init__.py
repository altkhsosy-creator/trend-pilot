# True Crime Music System — dynamic per-segment music selection

SEGMENT_MUSIC = {
    # Hooks — bgm_suspense for max tension at the start
    "hook_start":   "bgm_suspense.mp3",      # opening hook — immediate tension
    "hook_middle":  "bgm_investigative.mp3", # mid-story hook — building dread
    "hook_end":     "bgm_horror.mp3",        # climax hook — shock/horror

    # Story narration
    "story_normal": "bgm_calm.mp3",          # regular narration — calm, atmospheric
    "story_tension":"bgm_suspense.mp3",      # tension moments — suspenseful
    "story_climax": "bgm_horror.mp3",        # peak climax — horror/shock

    # Special moments
    "emotional":    "bgm_reflective.mp3",    # emotional beats — reflective
    "closing":      "bgm_mystery.mp3",       # haunting ending — lingering mystery
}


def get_music_for_segment(segment_type: str) -> str:
    """Returns the correct background music filename for a given segment type."""
    return SEGMENT_MUSIC.get(segment_type, "bgm_calm.mp3")
