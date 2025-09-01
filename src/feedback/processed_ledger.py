# src/feedback/processed_ledger.py

import json
import logging
from pathlib import Path
import hashlib
import threading

logger = logging.getLogger(__name__)

class ProcessedLedger:
    def __init__(self, site_identifier: str):
        self.filepath = Path("knowledge_base") / f"{site_identifier}_ledger.json"
        self.filepath.parent.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self.data = self._load()

    def _load(self) -> dict:
        try:
            with self._lock:
                if self.filepath.exists():
                    with open(self.filepath, 'r', encoding='utf-8') as f:
                        return json.load(f)
        except (IOError, json.JSONDecodeError): pass
        return {}

    def _save(self):
        try:
            with self._lock:
                with open(self.filepath, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"처리 기록부 저장 실패: {e}")

    def _get_content_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def add_processed_item(self, url: str, content_text: str):
        with self._lock:
            self.data[url] = self._get_content_hash(content_text)
        self._save()
        logger.debug(f"처리 기록부에 추가: {url}")

    def has_changed(self, url: str, new_content_text: str) -> bool:
        new_hash = self._get_content_hash(new_content_text)
        existing_hash = self.data.get(url)
        return existing_hash != new_hash