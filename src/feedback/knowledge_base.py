# src/feedback/knowledge_base.py

import json
import logging
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

class KnowledgeBase:
    def __init__(self, site_identifier: str):
        self.filepath = Path("knowledge_base") / f"{site_identifier}_kb.json"
        self.filepath.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self.data = self._load()

    def _load(self) -> defaultdict:
        try:
            with self._lock:
                if self.filepath.exists():
                    with open(self.filepath, 'r', encoding='utf-8') as f:
                        factory = lambda: {"total_score": 0, "count": 0, "avg_score": 0, "failure_count": 0}
                        return defaultdict(factory, json.load(f))
        except (IOError, json.JSONDecodeError): pass
        return defaultdict(lambda: {"total_score": 0, "count": 0, "avg_score": 0, "failure_count": 0})

    def _save(self):
        try:
            with self._lock:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"지식 베이스 저장 실패: {e}")

    def _get_pattern_from_url(self, url: str) -> str:
        try:
            path = urlparse(url).path
            return str(Path(path).parent) if '.' in path.split('/')[-1] else path
        except Exception: return "/"

    def update_score(self, url: str, score: float):
        pattern = self._get_pattern_from_url(url)
        if not pattern: return
        with self._lock:
            entry = self.data[pattern]
            entry["total_score"] += score
            entry["count"] += 1
            entry["avg_score"] = round(entry["total_score"] / entry["count"], 3)
        self._save()

    def update_failure(self, url: str):
        pattern = self._get_pattern_from_url(url)
        if not pattern: return
        with self._lock:
            self.data[pattern]["failure_count"] += 1
        self._save()
        logger.warning(f"🚨 파싱 실패 학습: '{pattern}' 경로의 실패 횟수 증가 -> {self.data[pattern]['failure_count']}회")

    def should_ignore(self, url: str, ignore_threshold: float = 0.4, min_samples: int = 3) -> bool:
        entry = self.data.get(self._get_pattern_from_url(url))
        return entry and entry["count"] >= min_samples and entry["avg_score"] < ignore_threshold

    def is_problematic(self, url: str, failure_threshold: int = 3) -> bool:
        entry = self.data.get(self._get_pattern_from_url(url))
        return entry and entry["failure_count"] >= failure_threshold