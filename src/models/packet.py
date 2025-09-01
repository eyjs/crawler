# src/models/packet.py

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

@dataclass
class SourceInfo:
    """크롤링 소스 정보"""
    site_identifier: str
    site_name: str
    base_url: str
    instruction_prompt: str

@dataclass
class Metadata:
    """메타데이터"""
    crawl_timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    data_expiry_date: str = field(default_factory=lambda: (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z")
    source_page_url: Optional[str] = None

@dataclass
class AttachmentInfo:
    """다운로드된 첨부파일 정보"""
    file_name: str
    original_url: str
    local_path: str # output 폴더 기준의 상대 경로
    file_type: str

@dataclass
class CrawledContent:
    """수집 및 강화된 콘텐츠"""
    content_url: str
    title: str
    extracted_text: str
    summary: str
    keywords: List[str]
    language: str = "ko"
    content_type: str = "web_page"
    relevance_score: float = 0.0
    attachments: List[AttachmentInfo] = field(default_factory=list)

@dataclass
class DataPacket:
    """백엔드 전송용 최종 데이터 패킷"""
    source_info: SourceInfo
    crawled_content: CrawledContent
    metadata: Metadata
    packet_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = "crawler-agent-01"