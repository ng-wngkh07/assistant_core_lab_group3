import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from assistant_core.errors import DataError


@dataclass(frozen=True)
class Office:
    name: str
    room: str
    hours: str


class OfficeDirectory:
    def __init__(self, offices: dict[str, Office]):
        self._offices = offices

    @classmethod
    def from_csv(cls, path: Path) -> "OfficeDirectory":
        try:
            with path.open(encoding="utf-8", newline="") as f:
                rows = list(csv.DictReader(f))
        except FileNotFoundError as exc:
            raise DataError(f"office file not found: {path}") from exc
        except (csv.Error, KeyError) as exc:
            raise DataError(f"malformed office file: {path}: {exc}") from exc
        return cls({r["name"].lower(): Office(r["name"], r["room"], r["hours"]) for r in rows})

    @property
    def names(self) -> set[str]:
        return set(self._offices)

    def find(self, text: str) -> Office | None:
        t = text.lower()
        return next((o for name, o in self._offices.items() if name in t), None)

    def all(self) -> list[Office]:
        return sorted(self._offices.values(), key=lambda o: o.name)


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    text: str
    keywords: list[str] = field(default_factory=list)


class Handbook:
    def __init__(self, rules: list[Rule]):
        self._rules = rules

    @classmethod
    def from_json(cls, path: Path) -> "Handbook":
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError as exc:
            raise DataError(f"handbook file not found: {path}") from exc
        except (json.JSONDecodeError, KeyError) as exc:
            raise DataError(f"malformed handbook file: {path}: {exc}") from exc

        rules = [
            Rule(
                id=item["id"],
                title=item["title"],
                text=item["text"],
                keywords=[k.lower() for k in item.get("keywords", [])],
            )
            for item in data
        ]
        return cls(rules)

    def search(self, query: str) -> Rule | None:
        stopwords = {
            "to",
            "the",
            "a",
            "an",
            "in",
            "on",
            "of",
            "for",
            "and",
            "or",
            "is",
            "are",
            "at",
            "by",
            "with",
            "how",
        }
        q_tokens = set(re.findall(r"\w+", query.lower())) - stopwords
        if not q_tokens:
            return None
        best_rule: Rule | None = None
        best_overlap = 0
        for rule in self._rules:
            rule_tokens = set(rule.keywords) | (set(re.findall(r"\w+", rule.title.lower())) - stopwords)
            overlap = len(q_tokens & rule_tokens)
            if overlap > best_overlap:
                best_overlap = overlap
                best_rule = rule
        return best_rule if best_overlap > 0 else None
