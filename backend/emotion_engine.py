"""
emotion_engine.py — Narration Optimization Layer
Rewrites scripts for natural spoken delivery, optimized for ElevenLabs documentary voices.
Controlled by ENABLE_EMOTION_ENGINE in .env
"""

import re
import logging
from config import ENABLE_EMOTION_ENGINE

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Detection keyword lists
# -------------------------------------------------------

_SUSPENSE_PHRASES = [
    "nobody expected", "no one expected", "what happened next",
    "what came next", "everything changed", "nothing would ever",
    "until that moment", "but then", "and then", "suddenly",
    "without warning", "out of nowhere", "at that exact moment",
    "that's when", "that is when", "before anyone could",
]

_SHOCK_PHRASES = [
    "changed everything", "shocked the", "terrifying", "impossible",
    "could not believe", "couldn't believe", "unbelievable",
    "the result", "the truth", "the answer", "the evidence",
    "what they found", "what was discovered", "turned out",
    "revealed that", "proved that", "confirmed that",
    "stunned", "horrified", "disturbing", "chilling",
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
    r"(study|research|report|survey|data)\s+(shows?|found|reveals?|suggests?|confirms?)",
    r"in \d{4}",
    r"for \d+ (years?|months?|days?|decades?)",
    r"(over|more than|at least|nearly|almost)\s+\d+",
]


# -------------------------------------------------------
# Helper detectors
# -------------------------------------------------------

def detect_suspense(sentence: str) -> bool:
    """Returns True if the sentence builds suspense or anticipation."""
    lower = sentence.lower()
    return any(phrase in lower for phrase in _SUSPENSE_PHRASES)


def detect_shock(sentence: str) -> bool:
    """Returns True if the sentence contains a shocking revelation or discovery."""
    lower = sentence.lower()
    return any(phrase in lower for phrase in _SHOCK_PHRASES)


def detect_question(sentence: str) -> bool:
    """Returns True if the sentence is a question (direct or rhetorical)."""
    stripped = sentence.strip()
    if stripped.endswith("?"):
        return True
    lower = stripped.lower()
    return any(lower.startswith(q) for q in _QUESTION_STARTERS)


def detect_fact(sentence: str) -> bool:
    """Returns True if the sentence contains a statistic or verifiable claim."""
    return any(re.search(pat, sentence, re.IGNORECASE) for pat in _FACT_PATTERNS)


# -------------------------------------------------------
# Sentence-level rewriters
# -------------------------------------------------------

def _rewrite_suspense(sentence: str) -> str:
    """
    Insert a pause before the climactic part of a suspense sentence.
    'Nobody expected what happened next.' →
    'Nobody expected… what happened next.'
    """
    triggers = [
        "what happened", "what came next", "everything changed",
        "nothing would", "that's when", "that is when",
        "but then", "and then", "suddenly", "without warning",
    ]
    lower = sentence.lower()
    for trigger in triggers:
        idx = lower.find(trigger)
        if idx > 8:  # only if there's actual content before it
            return sentence[:idx].rstrip() + "… " + sentence[idx:]
    return sentence


def _rewrite_shock(sentence: str) -> str:
    """
    Add pause before the impactful word/phrase.
    'The result changed everything.' → 'The result… changed everything.'
    """
    shock_pivots = [
        "changed everything", "shocked", "turned out", "revealed",
        "confirmed", "proved", "was not", "wasn't", "did not", "didn't",
    ]
    lower = sentence.lower()
    for pivot in shock_pivots:
        idx = lower.find(pivot)
        if 4 < idx < len(sentence) - 4:
            return sentence[:idx].rstrip() + "… " + sentence[idx:]
    return sentence


def _rewrite_question(sentence: str) -> str:
    """
    Prepend 'But ' to questions that don't already start with a conjunction.
    'What did they discover?' → 'But what did they discover?'
    """
    skip_prefixes = ("but ", "and ", "so ", "yet ", "still ", "then ")
    lower = sentence.lower()
    if any(lower.startswith(p) for p in skip_prefixes):
        return sentence
    return "But " + sentence[0].lower() + sentence[1:]


def _break_long_sentence(sentence: str) -> str:
    """
    Break sentences longer than ~25 words at natural spoken pause points.
    Preserves meaning. Adds '…' at split points for ElevenLabs breathing room.
    """
    words = sentence.split()
    if len(words) <= 22:
        return sentence

    # Natural break conjunctions / transition words
    break_words = [
        " — ", " — ", ", but ", ", and ", ", yet ", ", so ",
        ", which ", ", who ", ", where ", ", while ", ", because ",
        ", however ", ", although ", ", even though ",
    ]

    result = sentence
    for bw in break_words:
        if bw in result:
            # Only break once per sentence
            idx = result.find(bw)
            left = result[:idx].rstrip(" ,—")
            right = result[idx + len(bw):].lstrip()
            if len(left.split()) >= 6 and len(right.split()) >= 4:
                result = left + ".\n" + right[0].upper() + right[1:]
                return result

    # Fallback: split at comma after 15+ words
    parts = result.split(", ")
    if len(parts) >= 2:
        mid = len(parts) // 2
        left = ", ".join(parts[:mid])
        right = ", ".join(parts[mid:])
        if len(left.split()) >= 8:
            return left + ".\n" + right[0].upper() + right[1:]

    return sentence


# -------------------------------------------------------
# Main optimizer
# -------------------------------------------------------

def optimize_for_narration(script: str) -> str:
    """
    Rewrites a documentary script for optimal spoken narration delivery.
    Optimized for ElevenLabs documentary voices.

    Returns the optimized script unchanged if ENABLE_EMOTION_ENGINE=false.
    """
    if not ENABLE_EMOTION_ENGINE:
        logger.info("[emotion_engine] Disabled — returning original script unchanged")
        return script

    # Split into paragraphs first, then sentences within each
    paragraphs = script.split("\n\n")
    output_paragraphs = []

    stats = {
        "original_words": len(script.split()),
        "pauses_inserted": 0,
        "sentences_modified": 0,
    }

    for para in paragraphs:
        # Preserve mini-hook lines (inserted by retention_engine) as-is
        stripped = para.strip()
        if not stripped or len(stripped.split()) <= 4:
            output_paragraphs.append(para)
            continue

        # Split paragraph into sentences
        raw_sentences = re.split(r'(?<=[.!?])\s+', stripped)
        rewritten = []

        for sent in raw_sentences:
            sent = sent.strip()
            if not sent:
                continue

            original = sent
            modified = False

            # 1. Break very long sentences first
            sent = _break_long_sentence(sent)
            if sent != original:
                modified = True

            # 2. Apply type-specific rewrites to each resulting sub-sentence
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


# -------------------------------------------------------
# Unit tests
# -------------------------------------------------------

def _run_tests():
    print("\n=== emotion_engine unit tests ===\n")
    passed = failed = 0

    def check(name, result, expected_contains=None, should_change=True):
        nonlocal passed, failed
        changed = result != name
        ok = True
        if should_change and not changed:
            ok = False
        if not should_change and changed:
            ok = False
        if expected_contains and expected_contains not in result:
            ok = False
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {name[:60]}")
        if not ok:
            print(f"         got: {result[:80]}")

    # detect_suspense
    assert detect_suspense("Nobody expected what happened next."), "suspense failed"
    assert not detect_suspense("The weather was nice today."), "suspense false positive"
    print("  [PASS] detect_suspense")
    passed += 1

    # detect_shock
    assert detect_shock("The result changed everything."), "shock failed"
    assert not detect_shock("He walked to the store."), "shock false positive"
    print("  [PASS] detect_shock")
    passed += 1

    # detect_question
    assert detect_question("What did they discover?"), "question ? failed"
    assert detect_question("How could this happen"), "question no ? failed"
    assert not detect_question("He found the answer."), "question false positive"
    print("  [PASS] detect_question")
    passed += 1

    # detect_fact
    assert detect_fact("Over 3 million people were affected."), "fact number failed"
    assert detect_fact("According to the report, this is serious."), "fact 'according to' failed"
    assert not detect_fact("He walked outside."), "fact false positive"
    print("  [PASS] detect_fact")
    passed += 1

    # _rewrite_suspense
    r = _rewrite_suspense("Nobody expected what happened next.")
    check("Nobody expected what happened next.", r, "…")

    # _rewrite_shock
    r = _rewrite_shock("The result changed everything.")
    check("The result changed everything.", r, "…")

    # _rewrite_question
    r = _rewrite_question("What did they find?")
    check("What did they find?", r, "But ")

    r2 = _rewrite_question("But what did they find?")
    assert r2 == "But what did they find?", "question should not double-prefix"
    print("  [PASS] _rewrite_question no double prefix")
    passed += 1

    # optimize_for_narration (full pass)
    sample = (
        "Nobody expected what happened next. "
        "The result changed everything. "
        "What did they discover? "
        "Over 3 million people saw this."
    )
    result = optimize_for_narration(sample)
    assert "…" in result, "optimize should insert pauses"
    assert "But " in result, "optimize should add 'But' to questions"
    print("  [PASS] optimize_for_narration full pass")
    passed += 1

    print(f"\n  Results: {passed} passed, {failed} failed\n")
    return failed == 0


if __name__ == "__main__":
    _run_tests()
