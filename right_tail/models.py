from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

WEIGHTS: dict[str, int] = {"low": 1, "medium": 2, "high": 3, "critical": 4}

Priority = Literal["low", "medium", "high", "critical"]


@dataclass
class Comment:
    file: str
    priority: Priority
    message: str
    line: int | None = None
    suggestion: str = ""


@dataclass
class Attempt:
    branch: str
    attempt_id: int
    quality_score: int
    comments: list[Comment]
    weighted_penalty: int
    right_tail_score: int

    @classmethod
    def build(cls, branch: str, attempt_id: int, quality_score: int, comments: list[Comment]) -> "Attempt":
        penalty = sum(WEIGHTS[c.priority] for c in comments)
        return cls(
            branch=branch,
            attempt_id=attempt_id,
            quality_score=quality_score,
            comments=comments,
            weighted_penalty=penalty,
            right_tail_score=quality_score - penalty,
        )

    def has_blocking_comments(self) -> bool:
        return any(c.priority in ("high", "critical") for c in self.comments)
