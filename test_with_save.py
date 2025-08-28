"""
결과 저장 기능이 있는 크롤링 테스트
"""
import json
import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.crawler.hybrid_extractor import AsyncStyleContentExtractor
from src.llm.gemini_client import gemini_client

class ResultSaver:
    """테스트 결과 저장 클래스"""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name, url, goal, page_data, link_evaluations, errors=None):
        """결과 추가"""
        result = {
            'test_name': test_name,
            'url': url,
            'goal': goal,
            'timestamp': datetime.now().isoformat(),
            'page_load_success': page_data['success'],
            'content_length': page_data.get('content_length', 0),
            'total_links_found': page_data.get('links_count', 0),
            'links_evaluated': len(link_evaluations),
            'relevant_links': [eval for eval in link_evaluations if eval.get('is_relevant', False)],
            'link_evaluations': link_evaluations,
            'sample_content': page_data.get('content', '')[:500] + '...' if page_data.get('content') else '',
            'errors': errors or []
        }
        self.results.append(result)
    
    def save_results(self):
        """결과를 JSON 파일로 저장"""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # 결과 디렉토리 생성
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        # 상세 결과 저장
        detailed_file = results_dir / f"detailed_results_{timestamp}.json"
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump({
                'test_summary': {
                    'start_time': self.start_time.isoformat(),
                    'end_time': datetime.now().isoformat(),
                    'total_tests': len(self.results),
                    'successful_tests': sum(1 for r in self.results if r['page_load_success']),
                    'total_relevant_links': sum(len(r['relevant_links']) for r in self.results)
                },
                'detailed_results': self.results
            }, f, ensure_ascii=False, indent=2)
        
        # 요약 리포트 저장
        summary_file = results_dir / f"summary_report_{timestamp}.txt"
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("🚀 LLM 크롤링 테스트 결과 리포트\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"📅 테스트 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"🧪 총 테스트: {len(self.results)}개\n")
            f.write(f"✅ 성공: {sum(1 for r in self.results if r['page_load_success'])}개\n")
            f.write(f"🎯 발견된 관련 링크: {sum(len(r['relevant_links']) for r in self.results)}개\n\n")
            
            for i, result in enumerate(self.results, 1):
                f.write(f"📍 테스트 {i}: {result['test_name']}\n")
                f.write(f"   URL: {result['url']}\n")
                f.write(f"   목표: {result['goal']}\n")
                f.write(f"   상태: {'✅ 성공' if result['page_load_success'] else '❌ 실패'}\n")
                if result['page_load_success']:
                    f.write(f"   컨텐츠: {result['content_length']}자\n")
                    f.write(f"   전체 링크: {result['total_links_found']}개\n")
                    f.write(f"   평가된 링크: {result['links_evaluated']}개\n")
                    f.write(f"   관련 링크: {len(result['relevant_links'])}개\n")
                    
                    if result['relevant_links']:
                        f.write("   🎯 관련성 높은 링크들:\n")
                        for j, link in enumerate(result['relevant_links'][:3], 1):
                            f.write(f"      {j}. {link['text'][:50]}... (점수: {link['score']:.2f})\n")
                
                if result['errors']:
                    f.write(f"   ❌ 오류: {', '.join(result['errors'])}\n")
                f.write("\n")
        
        print(f"\n💾 결과 저장 완료:")
        print(f"   📄 상세 결과: {detailed_file}")
        print(f"   📋 요약 리포트: {summary_file}")
        
        return detailed_file, summary_file

async def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 LLM 기반 지능형 크롤링 테스트")
    print("=" * 60)
    
    saver = ResultSaver()
    
    # 설정 로드
    config_file = "test_configs/quick_test.json"
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"✅ 설정 파일 로드: {len(config['test_cases'])}개 테스트")
    except Exception as e:
        print(f"❌ 설정 파일 로드 실패: {e}")
        return
    
    # 크롤링 실행
    async with AsyncStyleContentExtractor(
        timeout=config['crawler_settings']['timeout'],
        delay=config['crawler_settings']['request_delay'],
        max_workers=3
    ) as extractor:
        
        for i, test_case in enumerate(config['test_cases'], 1):
            name = test_case['name']
            url = test_case['url']
            prompt = test_case['prompt']
            
            print(f"\n📍 테스트 {i}/{len(config['test_cases'])}: {name}")
            print(f"🌐 URL: {url}")
            
            errors = []
            link_evaluations = []
            
            try:
                # 페이지 로드
                print("📄 페이지 로딩...")
                page_data = await extractor.fetch_page_content(url)
                
                if not page_data['success']:
                    errors.append(f"페이지 로드 실패: {page_data['error']}")
                    print(f"❌ {errors[-1]}")
                else:
                    print(f"✅ 페이지 로드 성공! (컨텐츠: {page_data['content_length']}자, 링크: {page_data['links_count']}개)")
                    
                    # LLM 평가
                    if page_data['links']:
                        print("🤖 LLM 링크 평가 중...")
                        top_links = page_data['links'][:3]
                        
                        for j, link in enumerate(top_links, 1):
                            print(f"   {j}/3. {link['text'][:40]}...")
                            
                            try:
                                score = await gemini_client.evaluate_relevance_score(
                                    link_text=link['text'],
                                    url=link['url'],
                                    context=link['context'],
                                    target_goal=prompt
                                )
                                
                                is_relevant = score >= config['crawler_settings']['relevance_threshold']
                                
                                evaluation = {
                                    'text': link['text'],
                                    'url': link['url'],
                                    'score': score,
                                    'is_relevant': is_relevant
                                }
                                
                                link_evaluations.append(evaluation)
                                print(f"      점수: {score:.2f} {'✅' if is_relevant else '❌'}")
                                
                            except Exception as e:
                                errors.append(f"링크 평가 실패: {str(e)}")
                                print(f"      ❌ 평가 실패: {e}")
            
            except Exception as e:
                errors.append(f"테스트 실행 오류: {str(e)}")
                print(f"❌ 테스트 오류: {e}")
                page_data = {'success': False, 'content_length': 0, 'links_count': 0}
            
            # 결과 저장
            saver.add_result(name, url, prompt, page_data, link_evaluations, errors)
            
            # 테스트 간 간격
            if i < len(config['test_cases']):
                print("⏳ 다음 테스트까지 2초 대기...")
                await asyncio.sleep(2)
    
    # 최종 결과 저장
    print("\n" + "=" * 60)
    print("📊 테스트 완료 - 결과 저장 중...")
    detailed_file, summary_file = saver.save_results()
    
    # 간단한 요약 출력
    total_relevant = sum(len(r['relevant_links']) for r in saver.results)
    print(f"\n🎯 총 관련성 높은 링크: {total_relevant}개 발견")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
