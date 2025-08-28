"""
저장된 테스트 결과 확인
"""
import json
import os
from pathlib import Path
from datetime import datetime

def show_latest_results():
    """가장 최근 테스트 결과 표시"""
    results_dir = Path("test_results")
    
    if not results_dir.exists():
        print("❌ test_results 폴더가 없습니다.")
        print("먼저 test_with_save.py를 실행하세요.")
        return
    
    # 가장 최근 파일 찾기
    json_files = list(results_dir.glob("detailed_results_*.json"))
    txt_files = list(results_dir.glob("summary_report_*.txt"))
    
    if not json_files:
        print("❌ 저장된 테스트 결과가 없습니다.")
        return
    
    latest_json = max(json_files, key=os.path.getctime)
    latest_txt = max(txt_files, key=os.path.getctime) if txt_files else None
    
    print("=" * 60)
    print("📋 최근 테스트 결과")
    print("=" * 60)
    
    # 요약 리포트 출력
    if latest_txt:
        print("📄 요약 리포트:")
        print("-" * 40)
        with open(latest_txt, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
    
    # JSON 결과 간략히 출력
    try:
        with open(latest_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n📊 상세 결과 요약:")
        print("-" * 40)
        summary = data['test_summary']
        print(f"시작 시간: {summary['start_time']}")
        print(f"총 테스트: {summary['total_tests']}개")
        print(f"성공한 테스트: {summary['successful_tests']}개")
        print(f"발견된 관련 링크: {summary['total_relevant_links']}개")
        
        print("\n🔗 관련성 높은 링크들:")
        for i, result in enumerate(data['detailed_results'], 1):
            if result['relevant_links']:
                print(f"\n{i}. {result['test_name']}:")
                for link in result['relevant_links'][:2]:  # 상위 2개만
                    print(f"   ✅ {link['text'][:50]}... (점수: {link['score']:.2f})")
    
    except Exception as e:
        print(f"❌ 결과 파일 읽기 실패: {e}")
    
    print("\n" + "=" * 60)
    print(f"💾 결과 파일 위치:")
    print(f"📄 요약: {latest_txt}")
    print(f"📊 상세: {latest_json}")

if __name__ == "__main__":
    show_latest_results()
