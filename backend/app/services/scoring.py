"""Deterministic and explainable job-match scoring.

This module deliberately has no LLM, environment, I/O, or random dependencies.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Mapping, Sequence

DIMENSION_WEIGHTS: dict[str, Decimal] = {
    "core_skills": Decimal("0.45"),
    "preferred_skills": Decimal("0.15"),
    "project_experience": Decimal("0.20"),
    "education_background": Decimal("0.10"),
    "work_experience": Decimal("0.10"),
}

SKILL_STATUS_SCORES = {
    "matched": 100,
    "partial": 60,
    "unverified": 25,
    "missing": 0,
}

PROJECT_STATUS_SCORES = {
    "direct": 100,
    "related": 70,
    "general": 45,
    "unverified": 25,
    "missing": 0,
}

EVIDENCE_STATUS_SCORES = {
    "matched": 100,
    "partial": 60,
    "unverified": 25,
    "missing": 0,
}


def _rounded(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _key(value: str) -> str:
    return " ".join(value.split()).casefold()


def classify_required_skills(
    requirements: Sequence[str],
    matched_skills: Sequence[str],
    partial_skills: Sequence[str],
    missing_skills: Sequence[str],
    unverified_skills: Sequence[str],
) -> dict[str, list[str]]:
    """Put every required skill in exactly one deterministic status bucket."""
    status_sets = {
        "matched": {_key(item) for item in matched_skills},
        "partial": {_key(item) for item in partial_skills},
        "missing": {_key(item) for item in missing_skills},
        "unverified": {_key(item) for item in unverified_skills},
    }
    result = {status: [] for status in SKILL_STATUS_SCORES}
    seen: set[str] = set()
    for requirement in requirements:
        normalized = _key(requirement)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        # A fixed precedence makes contradictory model output harmless.
        status = "unverified"
        for candidate in ("matched", "partial", "missing", "unverified"):
            if normalized in status_sets[candidate]:
                status = candidate
                break
        result[status].append(requirement)
    return result


def _skill_score(classification: Mapping[str, Sequence[str]]) -> int:
    count = sum(len(items) for items in classification.values())
    if not count:
        return 0
    points = sum(
        len(classification[status]) * score
        for status, score in SKILL_STATUS_SCORES.items()
    )
    return _rounded(Decimal(points) / Decimal(count))


def _skill_reason(classification: Mapping[str, Sequence[str]]) -> str:
    return (
        f"共 {sum(len(items) for items in classification.values())} 项要求："
        f"匹配 {len(classification['matched'])}，部分匹配 {len(classification['partial'])}，"
        f"未核实 {len(classification['unverified'])}，明确缺失 {len(classification['missing'])}；"
        "固定计分依次为 100/60/25/0。"
    )


def calculate_match_score(
    *,
    core_skills: Sequence[str] = (),
    preferred_skills: Sequence[str] = (),
    project_requirements: Sequence[str] = (),
    education_requirements: Sequence[str] = (),
    experience_requirements: Sequence[str] = (),
    matched_skills: Sequence[str] = (),
    partial_skills: Sequence[str] = (),
    missing_skills: Sequence[str] = (),
    unverified_skills: Sequence[str] = (),
    project_status: str = "unverified",
    education_status: str = "unverified",
    experience_status: str = "unverified",
) -> dict[str, object]:
    """Calculate a 0-100 score solely from structured requirements and statuses."""
    core = classify_required_skills(
        core_skills, matched_skills, partial_skills, missing_skills, unverified_skills
    )
    preferred = classify_required_skills(
        preferred_skills, matched_skills, partial_skills, missing_skills, unverified_skills
    )

    raw_dimensions: dict[str, tuple[int, bool, str]] = {
        "core_skills": (
            _skill_score(core),
            bool(core_skills),
            _skill_reason(core) if core_skills else "岗位未提出核心技能要求，不参与计分。",
        ),
        "preferred_skills": (
            _skill_score(preferred),
            bool(preferred_skills),
            _skill_reason(preferred) if preferred_skills else "岗位未提出加分技能要求，不参与计分。",
        ),
        "project_experience": (
            PROJECT_STATUS_SCORES.get(project_status, 25),
            bool(project_requirements),
            f"项目要求已标记为 {project_status}，固定映射为 "
            f"{PROJECT_STATUS_SCORES.get(project_status, 25)} 分。"
            if project_requirements
            else "岗位未提出项目要求，不参与计分。",
        ),
        "education_background": (
            EVIDENCE_STATUS_SCORES.get(education_status, 25),
            bool(education_requirements),
            f"教育要求已标记为 {education_status}，固定映射为 "
            f"{EVIDENCE_STATUS_SCORES.get(education_status, 25)} 分。"
            if education_requirements
            else "岗位未提出学历或专业要求，不参与计分。",
        ),
        "work_experience": (
            EVIDENCE_STATUS_SCORES.get(experience_status, 25),
            bool(experience_requirements),
            f"工作经验要求已标记为 {experience_status}，固定映射为 "
            f"{EVIDENCE_STATUS_SCORES.get(experience_status, 25)} 分。"
            if experience_requirements
            else "岗位未提出工作或实习经验要求，不参与计分。",
        ),
    }

    active_weight = sum(
        DIMENSION_WEIGHTS[name]
        for name, (_, applicable, _) in raw_dimensions.items()
        if applicable
    )
    breakdown: dict[str, dict[str, object]] = {}
    weighted_total = Decimal("0")
    for name, (dimension_score, applicable, reason) in raw_dimensions.items():
        effective_weight = (
            DIMENSION_WEIGHTS[name] / active_weight
            if applicable and active_weight
            else Decimal("0")
        )
        weighted_total += Decimal(dimension_score) * effective_weight
        breakdown[name] = {
            "score": dimension_score,
            "weight": float(effective_weight),
            "applicable": applicable,
            "reason": reason,
        }

    score = _rounded(weighted_total) if active_weight else 0
    score = max(0, min(100, score))
    return {
        "score": score,
        "score_breakdown": breakdown,
        "classified_skills": {
            status: core[status] + preferred[status]
            for status in SKILL_STATUS_SCORES
        },
    }
