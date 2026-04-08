from __future__ import annotations

from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path
import json
import re
import time
from typing import Any, Callable, Literal


ACCENTED_CHARS = "àáâãäèéêëìíîïòóôõöùúûüÀÁÂÃÄÈÉÊËÌÍÎÒÓÔÕÖÙÚÛÜçÇñÑ'"
REPLACEMENT_CHARS = "aaaaaeeeeiiiiooooouuuuAAAAAEEEEIIIOOOOOUUUUcCnN "
ACCENT_TRANSLATION = str.maketrans(dict(zip(ACCENTED_CHARS, REPLACEMENT_CHARS)))
MULTISPACE_RE = re.compile(r"\s{2,}")
WHITESPACE_RE = re.compile(r"\s")
NON_ALNUM_RE = re.compile(r"[^a-z0-9 ]+")
EngineName = Literal["baseline", "fast"]


@dataclass(frozen=True)
class SchoolStudent:
    ra: str
    name: str
    normalized_name: str
    normalized_no_space: str
    tokens: tuple[str, ...]
    token_set: frozenset[str]
    first_token: str
    last_token: str
    initials: str


@dataclass(frozen=True)
class KhanStudent:
    kaid: str
    coach_nickname: str
    username: str | None
    resolved_username: str
    normalized_name: str
    normalized_no_space: str
    tokens: tuple[str, ...]
    token_set: frozenset[str]
    first_token: str
    last_token: str
    initials: str


@dataclass(frozen=True)
class MatchCandidate:
    school_name: str
    school_ra: str
    khan_name: str
    khan_username: str
    score: float


@dataclass(frozen=True)
class MatchResult:
    ra: str
    school_name: str
    khan_name: str | None
    khan_username: str | None
    score: float | None
    status: str


@dataclass(frozen=True)
class TieWarning:
    kind: str
    entity: str
    score: float
    contenders: list[str]


def reg_str(value: str, join_words: bool = False, normalize_spaces: bool = False) -> str:
    if not value:
        return ""

    normalized = value.translate(ACCENT_TRANSLATION).lower()
    normalized = normalized.replace(".", " ")
    normalized = NON_ALNUM_RE.sub(" ", normalized)
    if join_words:
        normalized = WHITESPACE_RE.sub("", normalized)
    elif normalize_spaces:
        normalized = MULTISPACE_RE.sub(" ", normalized)
    return normalized.strip()


def _tokenize(normalized_name: str) -> tuple[str, ...]:
    return tuple(part for part in normalized_name.split(" ") if part)


def _build_initials(tokens: tuple[str, ...]) -> str:
    return "".join(token[0] for token in tokens if token)


def _build_school_student(ra: str, name: str) -> SchoolStudent:
    normalized_name = reg_str(name, normalize_spaces=True)
    normalized_no_space = reg_str(name, join_words=True)
    tokens = _tokenize(normalized_name)
    return SchoolStudent(
        ra=str(ra),
        name=str(name),
        normalized_name=normalized_name,
        normalized_no_space=normalized_no_space,
        tokens=tokens,
        token_set=frozenset(tokens),
        first_token=tokens[0] if tokens else "",
        last_token=tokens[-1] if tokens else "",
        initials=_build_initials(tokens),
    )


def _build_khan_student(student: dict[str, Any]) -> KhanStudent:
    coach_nickname = str(student["coachNickname"])
    username = student.get("username")
    resolved_username = str(username) if username else coach_nickname
    normalized_name = reg_str(coach_nickname, normalize_spaces=True)
    normalized_no_space = reg_str(coach_nickname, join_words=True)
    tokens = _tokenize(normalized_name)
    return KhanStudent(
        kaid=str(student["kaid"]),
        coach_nickname=coach_nickname,
        username=str(username) if username else None,
        resolved_username=resolved_username,
        normalized_name=normalized_name,
        normalized_no_space=normalized_no_space,
        tokens=tokens,
        token_set=frozenset(tokens),
        first_token=tokens[0] if tokens else "",
        last_token=tokens[-1] if tokens else "",
        initials=_build_initials(tokens),
    )


def jaccard_index(s1: str, s2: str) -> float:
    set1 = {word for word in s1.split(" ") if word}
    set2 = {word for word in s2.split(" ") if word}

    if not set1 and not set2:
        return 1.0
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union else 0.0


def levenshtein_distance(s1: str, s2: str) -> int:
    if s1 == s2:
        return 0
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, char1 in enumerate(s1, start=1):
        current_row = [i]
        for j, char2 in enumerate(s2, start=1):
            insertion = previous_row[j] + 1
            deletion = current_row[j - 1] + 1
            substitution = previous_row[j - 1] + (char1 != char2)
            current_row.append(min(insertion, deletion, substitution))
        previous_row = current_row
    return previous_row[-1]


def lcs_length(s1: str, s2: str) -> int:
    if not s1 or not s2:
        return 0

    previous_row = [0] * (len(s2) + 1)
    for char1 in s1:
        current_row = [0]
        for j, char2 in enumerate(s2, start=1):
            if char1 == char2:
                current_row.append(previous_row[j - 1] + 1)
            else:
                current_row.append(max(previous_row[j], current_row[j - 1]))
        previous_row = current_row
    return previous_row[-1]


def smith_waterman(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0

    previous_row = [0.0] * (len(s2) + 1)
    best = 0.0
    for char1 in s1:
        current_row = [0.0]
        for j, char2 in enumerate(s2, start=1):
            value = previous_row[j - 1] + 1.0 if char1 == char2 else 0.0
            current_row.append(max(value, 0.0))
            best = max(best, current_row[j])
        previous_row = current_row
    return best


def score_pair_baseline(school: SchoolStudent, khan: KhanStudent) -> float:
    return (
        100 * jaccard_index(school.normalized_name, khan.normalized_name)
        + 100 * jaccard_index(school.normalized_no_space, khan.normalized_no_space)
        - levenshtein_distance(school.normalized_name, khan.normalized_name)
        + lcs_length(school.normalized_name, khan.normalized_name)
        + smith_waterman(school.normalized_name, khan.normalized_name)
    )


def _ratio(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def score_pair_fast(school: SchoolStudent, khan: KhanStudent) -> float:
    if not school.tokens or not khan.tokens:
        return 0.0

    token_overlap = len(school.token_set & khan.token_set)
    token_union = len(school.token_set | khan.token_set)
    token_jaccard = token_overlap / token_union if token_union else 0.0
    ordered_ratio = _ratio(school.normalized_name, khan.normalized_name)
    compact_ratio = _ratio(school.normalized_no_space, khan.normalized_no_space)

    sorted_school = " ".join(sorted(school.tokens))
    sorted_khan = " ".join(sorted(khan.tokens))
    unordered_ratio = _ratio(sorted_school, sorted_khan)

    score = 0.0
    score += token_jaccard * 120
    score += ordered_ratio * 90
    score += compact_ratio * 120
    score += unordered_ratio * 70

    if school.first_token and school.first_token == khan.first_token:
        score += 20
    if school.last_token and school.last_token == khan.last_token:
        score += 15
    if school.initials and school.initials == khan.initials:
        score += 12

    if school.normalized_no_space.startswith(khan.normalized_no_space) or khan.normalized_no_space.startswith(
        school.normalized_no_space
    ):
        score += 25

    if token_overlap == min(len(school.token_set), len(khan.token_set)):
        score += 18

    score -= abs(len(school.tokens) - len(khan.tokens)) * 3
    score -= abs(len(school.normalized_no_space) - len(khan.normalized_no_space)) * 0.6
    return score


def load_json_file(file_path: str | Path) -> Any:
    path = Path(file_path)
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_school_students(etapa_ea_payload: dict[str, Any], class_name: str) -> list[SchoolStudent]:
    class_payload = etapa_ea_payload[class_name]
    students: list[SchoolStudent] = []
    seen_names: set[str] = set()
    seen_ra: set[str] = set()

    for row in class_payload["rows"]:
        ra, name = row[0], row[1]
        if ra in seen_ra:
            raise ValueError(f"RA duplicado na turma {class_name}: {ra}")
        if name in seen_names:
            raise ValueError(f"Aluno duplicado na turma {class_name}: {name}")

        seen_ra.add(ra)
        seen_names.add(name)
        students.append(_build_school_student(str(ra), str(name)))

    return students


def build_khan_students(roster_payload: dict[str, Any]) -> list[KhanStudent]:
    students: list[KhanStudent] = []
    seen_ids: set[str] = set()

    for student in roster_payload["students"]:
        kaid = str(student["kaid"])
        if kaid in seen_ids:
            raise ValueError(f"Aluno duplicado no roster Khan: {kaid}")
        seen_ids.add(kaid)
        students.append(_build_khan_student(student))

    return students


def _get_score_function(engine: EngineName) -> Callable[[SchoolStudent, KhanStudent], float]:
    if engine == "baseline":
        return score_pair_baseline
    if engine == "fast":
        return score_pair_fast
    raise ValueError(f"Engine invalida: {engine}")


def _top_candidates_by_khan(
    school_students: list[SchoolStudent],
    khan_students: list[KhanStudent],
    score_fn: Callable[[SchoolStudent, KhanStudent], float],
) -> tuple[dict[str, list[MatchCandidate]], list[MatchCandidate]]:
    candidates_by_khan: dict[str, list[MatchCandidate]] = {}
    all_candidates: list[MatchCandidate] = []

    for khan in khan_students:
        khan_candidates = [
            MatchCandidate(
                school_name=school.name,
                school_ra=school.ra,
                khan_name=khan.coach_nickname,
                khan_username=khan.resolved_username,
                score=score_fn(school, khan),
            )
            for school in school_students
        ]
        khan_candidates.sort(key=lambda item: (-item.score, item.school_name, item.school_ra))
        candidates_by_khan[khan.kaid] = khan_candidates
        all_candidates.extend(khan_candidates)

    return candidates_by_khan, all_candidates


def _resolve_matches(
    school_students: list[SchoolStudent],
    khan_students: list[KhanStudent],
    candidates_by_khan: dict[str, list[MatchCandidate]],
    all_candidates: list[MatchCandidate],
    min_score: float | None,
) -> dict[str, Any]:
    khan_by_username = {khan.resolved_username: khan for khan in khan_students}
    warnings: list[TieWarning] = []
    blocked_khan_ids: set[str] = set()

    for khan in khan_students:
        candidates = candidates_by_khan[khan.kaid]
        if not candidates:
            continue

        top_score = candidates[0].score
        tied = [item for item in candidates if item.score == top_score]
        if len(tied) > 1:
            blocked_khan_ids.add(khan.kaid)
            warnings.append(
                TieWarning(
                    kind="khan_top_tie",
                    entity=khan.coach_nickname,
                    score=top_score,
                    contenders=[item.school_name for item in tied],
                )
            )

    blocked_usernames = {
        khan.resolved_username for khan in khan_students if khan.kaid in blocked_khan_ids
    }

    school_best_scores: dict[str, float] = {}
    school_best_contenders: dict[str, list[MatchCandidate]] = {}
    for candidate in all_candidates:
        if candidate.khan_username in blocked_usernames:
            continue
        if min_score is not None and candidate.score < min_score:
            continue

        current_best = school_best_scores.get(candidate.school_ra)
        if current_best is None or candidate.score > current_best:
            school_best_scores[candidate.school_ra] = candidate.score
            school_best_contenders[candidate.school_ra] = [candidate]
        elif candidate.score == current_best:
            school_best_contenders[candidate.school_ra].append(candidate)

    blocked_school_ras: set[str] = set()
    for contenders in school_best_contenders.values():
        if len(contenders) > 1:
            blocked_school_ras.add(contenders[0].school_ra)
            warnings.append(
                TieWarning(
                    kind="school_top_tie",
                    entity=contenders[0].school_name,
                    score=contenders[0].score,
                    contenders=[item.khan_name for item in contenders],
                )
            )

    assigned_school_ras: set[str] = set()
    assigned_usernames: set[str] = set()
    accepted_pairs: list[MatchCandidate] = []

    sorted_candidates = sorted(
        all_candidates,
        key=lambda item: (-item.score, item.school_name, item.khan_username),
    )

    for candidate in sorted_candidates:
        if candidate.khan_username in blocked_usernames:
            continue
        if candidate.school_ra in blocked_school_ras:
            continue
        if min_score is not None and candidate.score < min_score:
            continue
        if candidate.school_ra in assigned_school_ras or candidate.khan_username in assigned_usernames:
            continue

        best_for_khan = candidates_by_khan[khan_by_username[candidate.khan_username].kaid][0]
        if candidate.school_ra != best_for_khan.school_ra or candidate.score != best_for_khan.score:
            continue

        accepted_pairs.append(candidate)
        assigned_school_ras.add(candidate.school_ra)
        assigned_usernames.add(candidate.khan_username)

    accepted_by_ra = {candidate.school_ra: candidate for candidate in accepted_pairs}
    results: list[MatchResult] = []
    for school in school_students:
        accepted = accepted_by_ra.get(school.ra)
        if accepted:
            results.append(
                MatchResult(
                    ra=school.ra,
                    school_name=school.name,
                    khan_name=accepted.khan_name,
                    khan_username=accepted.khan_username,
                    score=accepted.score,
                    status="matched",
                )
            )
        else:
            results.append(
                MatchResult(
                    ra=school.ra,
                    school_name=school.name,
                    khan_name=None,
                    khan_username=None,
                    score=None,
                    status="unmatched",
                )
            )

    unmatched_khan = [
        {"khanName": khan.coach_nickname, "khanUsername": khan.resolved_username}
        for khan in khan_students
        if khan.resolved_username not in assigned_usernames
    ]

    return {
        "matchedCount": len(accepted_pairs),
        "results": [asdict(result) for result in results],
        "warnings": [asdict(warning) for warning in warnings],
        "unmatchedKhan": unmatched_khan,
    }


def match_students(
    etapa_ea_payload: dict[str, Any],
    roster_payload: dict[str, Any],
    class_name: str,
    min_score: float | None = None,
    engine: EngineName = "baseline",
) -> dict[str, Any]:
    school_students = build_school_students(etapa_ea_payload, class_name)
    khan_students = build_khan_students(roster_payload)
    score_fn = _get_score_function(engine)
    candidates_by_khan, all_candidates = _top_candidates_by_khan(
        school_students,
        khan_students,
        score_fn,
    )
    resolved = _resolve_matches(
        school_students,
        khan_students,
        candidates_by_khan,
        all_candidates,
        min_score,
    )

    return {
        "className": class_name,
        "rosterName": roster_payload.get("name"),
        "engine": engine,
        "schoolStudentCount": len(school_students),
        "khanStudentCount": len(khan_students),
        **resolved,
    }


def benchmark_matchers(
    etapa_ea_payload: dict[str, Any],
    roster_payload: dict[str, Any],
    class_name: str,
    min_score: float | None = None,
    repetitions: int = 50,
) -> dict[str, Any]:
    benchmark: dict[str, Any] = {}

    for engine in ("baseline", "fast"):
        started = time.perf_counter()
        last_result = None
        for _ in range(repetitions):
            last_result = match_students(
                etapa_ea_payload=etapa_ea_payload,
                roster_payload=roster_payload,
                class_name=class_name,
                min_score=min_score,
                engine=engine,
            )
        elapsed = time.perf_counter() - started
        benchmark[engine] = {
            "secondsTotal": elapsed,
            "secondsPerRun": elapsed / repetitions,
            "matchedCount": last_result["matchedCount"] if last_result else 0,
            "warnings": len(last_result["warnings"]) if last_result else 0,
        }

    baseline_result = match_students(
        etapa_ea_payload=etapa_ea_payload,
        roster_payload=roster_payload,
        class_name=class_name,
        min_score=min_score,
        engine="baseline",
    )
    fast_result = match_students(
        etapa_ea_payload=etapa_ea_payload,
        roster_payload=roster_payload,
        class_name=class_name,
        min_score=min_score,
        engine="fast",
    )

    baseline_pairs = {
        row["school_name"]: row["khan_username"]
        for row in baseline_result["results"]
        if row["khan_username"]
    }
    fast_pairs = {
        row["school_name"]: row["khan_username"]
        for row in fast_result["results"]
        if row["khan_username"]
    }

    differing_students = sorted(
        {
            school_name
            for school_name in set(baseline_pairs) | set(fast_pairs)
            if baseline_pairs.get(school_name) != fast_pairs.get(school_name)
        }
    )

    return {
        "className": class_name,
        "repetitions": repetitions,
        "baseline": benchmark["baseline"],
        "fast": benchmark["fast"],
        "sameAssignments": not differing_students,
        "differentStudents": differing_students,
    }
