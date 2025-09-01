# src/packet/data_packet.py

import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any

def create_data_packet(agent_id: str, config: Dict[str, Any], page_data: Dict[str, Any], extracted_text: str, relevance_score: float, enhanced_data: Dict[str, Any]) -> Dict[str, Any]:
    crawl_timestamp = datetime.utcnow()
    return {
        "packetId": str(uuid.uuid4()),
        "agentId": agent_id,
        "sourceInfo": {
            "siteIdentifier": config.get("site_identifier"),
            "siteName": config.get("site_name"),
            "baseUrl": config.get("base_url"),
            "instructionPrompt": config.get("instruction_prompt")
        },
        "crawledContent": {
            "contentUrl": page_data.get("url"),
            "contentType": "webpage_text",
            "title": page_data.get("title"),
            "extractedText": extracted_text[:500] + ("..." if len(extracted_text) > 500 else ""),
            "relevanceScore": relevance_score,
            "language": enhanced_data.get("language"),
            "summary": enhanced_data.get("summary"),
            "keywords": enhanced_data.get("keywords")
        },
        "metadata": {
            "crawlTimestamp": crawl_timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "dataExpiryDate": (crawl_timestamp + timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "sourcePageUrl": page_data.get("url")
        }
    }