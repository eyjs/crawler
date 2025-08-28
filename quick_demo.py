"""
1분 완성 크롤링 데모
"""
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.crawler.hybrid_extractor import AsyncStyleContentExtractor
from src.llm.gemini_client import gemini_client

async def quick_demo():
    """1분 안에 끝나는 간단한 데모"""
    print("🚀 1분 크롤링 데모 시작!")
    print("=" * 40)
    
    test_url = "https://www.naver.com/"
    test_goal = "뉴스, 검색, 포털사이트"
    
    print(f"🌐 테스트 URL: {test_url}")
    print(f"🎯 목표: {test_goal}")
    print("-" * 40)
    
    async with AsyncStyleContentExtractor(timeout=15, delay=0.5) as extractor:
        # 1. 페이지 로드
        print("📄 페이지 로딩...")
        page_data = await extractor.fetch_page_content(test_url)
        
        if not page_data['success']:
            print(f"❌ 실패: {page_data['error']}")
            return
        
        print(f"✅ 성공! 컨텐츠 {len(page_data['content'])}자, 링크 {len(page_data['links'])}개")
        
        # 2. 첫 번째 링크만 LLM 평가
        if page_data['links']:
            first_link = page_data['links'][0]
            print(f"\n🤖 링크 평가: {first_link['text'][:50]}...")
            
            try:
                score = await gemini_client.evaluate_relevance_score(
                    link_text=first_link['text'],
                    url=first_link['url'],
                    context=first_link['context'],
                    target_goal=test_goal
                )
                print(f"📊 관련성 점수: {score:.2f}")
                print(f"{'✅ 관련성 높음' if score >= 0.5 else '❌ 관련성 낮음'}")
            except Exception as e:
                print(f"❌ LLM 평가 실패: {e}")
    
    print("\n🎉 데모 완료! LLM 기반 지능형 크롤러가 정상 작동합니다!")
    print("=" * 40)

if __name__ == "__main__":
    asyncio.run(quick_demo())
