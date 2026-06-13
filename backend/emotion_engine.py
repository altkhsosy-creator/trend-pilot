"""
emotion_engine.py — Narration Optimization Layer
Rewrites scripts for natural spoken delivery, optimized for ElevenLabs documentary voices.
True Crime Edition: dramatic pauses before hooks, after shocking revelations.
"""

import re
import logging
from config import ENABLE_EMOTION_ENGINE

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Detection keyword lists — True Crime enhanced
# -------------------------------------------------------

_SUSPENSE_PHRASES = [
    "nobody expected", "no one expected", "what happened next",
    "what came next", "everything changed", "nothing would ever",
    "until that moment", "but then", "and then", "suddenly",
    "without warning", "out of nowhere", "at that exact moment",
    "that's when", "that is when", "before anyone could",
    # True Crime additions
    "here's what investigators found", "here's the detail",
    "what the evidence showed", "what the forensics revealed",
    "what the FBI never addressed", "here's what gets me",
    "the detail i can't stop thinking about",
    "stop and think about what that means",
]

_SHOCK_PHRASES = [
    "changed everything", "shocked the", "terrifying", "impossible",
    "could not believe", "couldn't believe", "unbelievable",
    "the result", "the truth", "the answer", "the evidence",
    "what they found", "what was discovered", "turned out",
    "revealed that", "proved that", "confirmed that",
    "stunned", "horrified", "disturbing", "chilling",
    # True Crime additions
    "was murdered", "had been killed", "the body was",
    "the killer", "was not a suicide", "was not an accident",
    "the confession", "was arrested", "was identified",
    "the dna matched", "was found dead", "had been missing",
    "the autopsy showed", "forensic analysis confirmed",
    "the last entry", "the final call", "the last text",
]

_QUESTION_STARTERS = (
    "what ", "who ", "where ", "when ", "why ", "how ",
    "could ", "would ", "did ", "does ", "is there ", "are there ",
    "was it ", "were they ", "can anyone ",
)

_FACT_PATTERNS = [
    r"\d+\s*%",
    r"\d+\s*(million|billion|thousand|hundred)",
    r"according to",
    r"(study|research|report|survey|data|forensic|autopsy)\s+(shows?|found|reveals?|suggests?|confirms?)",
    r"in \d{4}",
    r"for \d+ (years?|months?|days?|decades?)",
    r"(over|more than|at least|nearly|almost)\s+\d+",
]

# True Crime specific — phrases that ALWAYS get a pause before them
_TRUE_CRIME_REVELATION_TRIGGERS = [
    "was not a suicide",
    "was not an accident",
    "the killer had been",
    "investigators found",
    "the body was found",
    "the confession revealed",
    "dna matched",
    "the final entry",
    "the last text",
    "nobody knows",
    "still unidentified",
    "never explained",
    "case remains open",
    "was living next door",
    "had been watching",
]


# -------------------------------------------------------
# Helper detectors
# -------------------------------------------------------

def detect_suspense(sentence: str) -> bool:
    lower = sentence.lower()
    return any(phrase in lower for phrase in _SUSPENSE_PHRASES)


def detect_shock(sentence: str) -> bool:
    lower = sentence.lower()
    return any(phrase in lower for phrase in _SHOCK_PHRASES)


def detect_question(sentence: str) -> bool:
    stripped = sentence.strip()
    if stripped.endswith("?"):
        return True
    lower = stripped.lower()
    return any(lower.startswith(q) for q in _QUESTION_STARTERS)


def detect_fact(sentence: str) -> bool:
    return any(re.search(pat, sentence, re.IGNORECASE) for pat in _FACT_PATTERNS)


def detect_true_crime_revelation(sentence: str) -> bool:
    """Returns True if sentence contains a True Crime revelation that needs a dramatic pause."""
    lower = sentence.lower()
    return any(trigger in lower for trigger in _TRUE_CRIME_REVELATION_TRIGGERS)


# -------------------------------------------------------
# Sentence-level rewriters
# -------------------------------------------------------

def _rewrite_suspense(sentence: str) -> str:
    triggers = [
        "what happened", "what came next", "everything changed",
        "nothing would", "that's when", "that is when",
        "but then", "and then", "suddenly", "without warning",
        "here's what", "here is what",
    ]
    lower = sentence.lower()
    for trigger in triggers:
        idx = lower.find(trigger)
        if idx > 8:
            return sentence[:idx].rstrip() + "… " + sentence[idx:]
    return sentence


def _rewrite_shock(sentence: str) -> str:
    shock_pivots = [
        "changed everything", "shocked", "turned out", "revealed",
        "confirmed", "proved", "was not", "wasn't", "did not", "didn't",
        "the killer", "the body", "the confession", "the evidence",
        "was murdered", "had been killed",
    ]
    lower = sentence.lower()
    for pivot in shock_pivots:
        idx = lower.find(pivot)
        if 4 < idx < len(sentence) - 4:
            return sentence[:idx].rstrip() + "… " + sentence[idx:]
    return sentence


def _rewrite_question(sentence: str) -> str:
    skip_prefixes = ("but ", "and ", "so ", "yet ", "still ", "then ")
    lower = sentence.lower()
    if any(lower.startswith(p) for p in skip_prefixes):
        return sentence
    return "But " + sentence[0].lower() + sentence[1:]


def _break_long_sentence(sentence: str) -> str:
    words = sentence.split()
    if len(words) <= 22:
        return sentence

    break_words = [
        " — ", " — ", ", but ", ", and ", ", yet ", ", so ",
        ", which ", ", who ", ", where ", ", while ", ", because ",
        ", however ", ", although ", ", even though ",
    ]

    result = sentence
    for bw in break_words:
        if bw in result:
            idx = result.find(bw)
            left = result[:idx].rstrip(" ,—")
            right = result[idx + len(bw):].lstrip()
            if len(left.split()) >= 6 and len(right.split()) >= 4:
                result = left + ".\n" + right[0].upper() + right[1:]
                return result

    parts = result.split(", ")
    if len(parts) >= 2:
        mid = len(parts) // 2
        left = ", ".join(parts[:mid])
        right = ", ".join(parts[mid:])
        if len(left.split()) >= 8:
            return left + ".\n" + right[0].upper() + right[1:]

    return sentence


def add_pre_hook_pauses(script: str) -> str:
    """
    Inserts a dramatic pause (…) before every ✨ hook marker.
    Searches back through blank lines to find the last non-empty line and appends "…".
    """
    lines = script.split("\n")
    result = list(lines)
    for i, line in enumerate(lines):
        if line.strip().startswith("✨") and i > 0:
            # Walk back through result to find last non-empty line
            for j in range(i - 1, -1, -1):
                prev = result[j].rstrip()
                if prev:  # non-empty line found
                    if not prev.endswith("…") and not prev.endswith("..."):
                        result[j] = prev + "…"
                    break
    return "\n".join(result)


def add_post_shock_pauses(script: str) -> str:
    """
    Inserts a beat pause (…) after shocking True Crime revelations.
    Gives listeners a moment to absorb what was just said.
    """
    sentences = re.split(r'(?<=[.!?])\s+', script)
    result = []
    for sent in sentences:
        if detect_true_crime_revelation(sent) and not sent.rstrip().endswith("…"):
            result.append(sent.rstrip() + "…")
        else:
            result.append(sent)
    return " ".join(result)


# -------------------------------------------------------
# Main optimizer
# -------------------------------------------------------

def optimize_for_narration(script: str) -> str:
    """
    Rewrites a True Crime script for optimal spoken narration delivery.
    Adds dramatic pauses before hooks, after shocking revelations, and at key moments.
    Returns unchanged if ENABLE_EMOTION_ENGINE=false.
    """
    if not ENABLE_EMOTION_ENGINE:
        logger.info("[emotion_engine] Disabled — returning original script unchanged")
        return script

    # Step 1: Add pre-hook pauses (before ✨ markers)
    script = add_pre_hook_pauses(script)

    # Step 2: Add post-shock pauses (after True Crime revelations)
    script = add_post_shock_pauses(script)

    # Step 3: Standard sentence-level optimization
    paragraphs = script.split("\n\n")
    output_paragraphs = []

    stats = {
        "original_words": len(script.split()),
        "pauses_inserted": 0,
        "sentences_modified": 0,
    }

    for para in paragraphs:
        stripped = para.strip()
        # Preserve hook lines and very short lines as-is
        if not stripped or len(stripped.split()) <= 4:
            output_paragraphs.append(para)
            continue
        if stripped.startswith("✨"):
            output_paragraphs.append(para)
            continue

        raw_sentences = re.split(r'(?<=[.!?])\s+', stripped)
        rewritten = []

        for sent in raw_sentences:
            sent = sent.strip()
            if not sent:
                continue

            original = sent
            modified = False

            sent = _break_long_sentence(sent)
            if sent != original:
                modified = True

            sub_sentences = sent.split("\n")
            new_subs = []
            for sub in sub_sentences:
                sub = sub.strip()
                if not sub:
                    continue
                orig_sub = sub

                if detect_suspense(sub):
                    sub = _rewrite_suspense(sub)
                    if sub != orig_sub:
                        stats["pauses_inserted"] += 1
                        modified = True
                elif detect_shock(sub):
                    sub = _rewrite_shock(sub)
                    if sub != orig_sub:
                        stats["pauses_inserted"] += 1
                        modified = True
                elif detect_question(sub):
                    sub = _rewrite_question(sub)
                    if sub != orig_sub:
                        modified = True

                new_subs.append(sub)

            rewritten.append(" ".join(new_subs))
            if modified:
                stats["sentences_modified"] += 1

        output_paragraphs.append(" ".join(rewritten))

    optimized = "\n\n".join(output_paragraphs)
    stats["optimized_words"] = len(optimized.split())

    logger.info(
        "[emotion_engine] Optimization complete | "
        "original_words=%d | optimized_words=%d | "
        "pauses_inserted=%d | sentences_modified=%d",
        stats["original_words"],
        stats["optimized_words"],
        stats["pauses_inserted"],
        stats["sentences_modified"],
    )
    print(
        f"[emotion_engine] original={stats['original_words']}w "
        f"optimized={stats['optimized_words']}w "
        f"pauses={stats['pauses_inserted']} "
        f"modified={stats['sentences_modified']}"
    )

    return optimized


if __name__ == "__main__":
    sample = """
In 1970, a woman was found dead in a valley.

✨ Nobody knew who she was. ✨

The autopsy showed she was not a suicide. The killer had been watching her for weeks. But then investigators found something that changed the entire case.

What did they discover? And why does no one talk about it?
""".strip()
    result = optimize_for_narration(sample)
    print(result)
