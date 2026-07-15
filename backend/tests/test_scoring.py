"""Unit tests for deterministic job-match scoring."""

from backend.app.services.scoring import (
    DIMENSION_WEIGHTS,
    calculate_match_score,
)


def score(**overrides):
    values = {
        "core_skills": ["Python", "SQL"],
        "preferred_skills": ["Redis"],
        "project_requirements": ["Backend API"],
        "education_requirements": ["Bachelor degree"],
        "experience_requirements": ["2 years"],
        "matched_skills": ["Python"],
        "partial_skills": ["SQL"],
        "unverified_skills": ["Redis"],
        "project_status": "related",
        "education_status": "matched",
        "experience_status": "partial",
    }
    values.update(overrides)
    return calculate_match_score(**values)


def test_identical_input_is_identical() -> None:
    assert score() == score()


def test_new_matched_core_skill_increases_score() -> None:
    before = score()
    after = score(matched_skills=["Python", "SQL"], partial_skills=[])
    assert after["score"] > before["score"]


def test_skill_status_ordering() -> None:
    matched = score(core_skills=["Python"], matched_skills=["Python"])
    partial = score(core_skills=["Python"], matched_skills=[], partial_skills=["Python"])
    unverified = score(
        core_skills=["Python"], matched_skills=[], partial_skills=[], unverified_skills=["Python"]
    )
    missing = score(
        core_skills=["Python"], matched_skills=[], partial_skills=[],
        unverified_skills=[], missing_skills=["Python"]
    )
    scores = [
        item["score_breakdown"]["core_skills"]["score"]
        for item in (matched, partial, unverified, missing)
    ]
    assert scores == [100, 60, 25, 0]


def test_no_work_requirement_does_not_penalize() -> None:
    result = score(experience_requirements=[], experience_status="missing")
    dimension = result["score_breakdown"]["work_experience"]
    assert dimension["applicable"] is False
    assert dimension["weight"] == 0


def test_no_education_requirement_does_not_penalize() -> None:
    result = score(education_requirements=[], education_status="missing")
    dimension = result["score_breakdown"]["education_background"]
    assert dimension["applicable"] is False
    assert dimension["weight"] == 0


def test_core_skills_have_highest_base_weight() -> None:
    assert DIMENSION_WEIGHTS["core_skills"] == max(DIMENSION_WEIGHTS.values())


def test_score_equals_renormalized_weighted_breakdown() -> None:
    result = score(education_requirements=[], experience_requirements=[])
    dimensions = result["score_breakdown"].values()
    expected = round(sum(item["score"] * item["weight"] for item in dimensions))
    assert result["score"] == expected
    assert abs(sum(item["weight"] for item in dimensions) - 1.0) < 1e-12


def test_score_always_in_range() -> None:
    assert 0 <= score()["score"] <= 100
    assert calculate_match_score()["score"] == 0


def test_free_model_score_cannot_be_passed_to_scoring_function() -> None:
    assert "score" not in calculate_match_score.__annotations__
