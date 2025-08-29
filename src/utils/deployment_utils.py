import os
import sys
import platform
from pathlib import Path
from loguru import logger

# Windows 콘솔 한글 출력 문제 해결
if os.name == 'nt':  # Windows
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

class PathManager:
    """크로스 플랫폼 exe/app 배포를 위한 경로 관리 클래스"""
    
    def __init__(self):
        # 현재 플랫폼 정보
        self.platform = platform.system().lower()
        
        # exe 파일/앱의 실제 위치를 기준으로 경로 설정
        if getattr(sys, 'frozen', False):
            # PyInstaller로 빌드된 환경
            if self.platform == 'darwin':  # macOS
                if sys.executable.endswith('.app/Contents/MacOS/WebCrawler'):
                    # .app 번들 내부에서 실행되는 경우
                    self.base_dir = Path(sys.executable).parent.parent.parent.parent
                else:
                    # 단일 실행파일인 경우
                    self.base_dir = Path(sys.executable).parent
            else:
                # Windows, Linux
                self.base_dir = Path(sys.executable).parent
        else:
            # 개발 환경
            self.base_dir = Path(__file__).parent.parent.parent
        
        # 필요한 폴더 경로들 정의
        self.input_dir = self.base_dir / "input"
        self.output_dir = self.base_dir / "output"
        self.logs_dir = self.base_dir / "logs"
        self.config_dir = self.base_dir / "config"
        
        logger.debug(f"플랫폼: {self.platform}")
        logger.debug(f"기준 디렉토리: {self.base_dir}")
        
    def ensure_directories(self):
        """필요한 모든 디렉토리를 생성합니다."""
        directories = {
            "input": self.input_dir,
            "output": self.output_dir, 
            "logs": self.logs_dir,
            "config": self.config_dir
        }
        
        created_dirs = []
        for name, path in directories.items():
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(name)
                    logger.info(f"📁 '{name}' 폴더 생성: {path}")
                except PermissionError as e:
                    logger.error(f"❌ '{name}' 폴더 생성 권한 없음: {e}")
                    if self.platform == 'darwin':
                        logger.info("💡 macOS: 시스템 환경설정 → 보안 및 개인정보 → 파일 및 폴더 접근 권한 확인")
                except Exception as e:
                    logger.error(f"❌ '{name}' 폴더 생성 실패: {e}")
            else:
                logger.debug(f"📁 '{name}' 폴더 존재: {path}")
        
        if created_dirs:
            logger.success(f"✅ 폴더 생성 완료: {', '.join(created_dirs)}")
        else:
            logger.info("✅ 모든 필요한 폴더가 이미 존재합니다")
            
        return True
    
    def create_sample_input_file(self):
        """샘플 입력 파일을 생성합니다 (없을 경우에만)"""
        sample_file = self.input_dir / "sample_input.xlsx"
        
        if not sample_file.exists():
            try:
                import pandas as pd
                
                # 샘플 데이터 생성
                sample_data = {
                    '기관/단체/회사': [
                        '샘플 회사 A', 
                        '샘플 기관 B', 
                        '샘플 단체 C'
                    ],
                    '주요 내용': [
                        '회사 소개 및 주요 사업 분야',
                        '기관 연혁 및 주요 업무',
                        '단체 활동 현황 및 공지사항'
                    ],
                    '웹사이트 주소': [
                        'https://example1.com',
                        'https://example2.com', 
                        'https://example3.com'
                    ]
                }
                
                df = pd.DataFrame(sample_data)
                df.to_excel(sample_file, index=False, engine='openpyxl')
                
                logger.success(f"📄 샘플 입력 파일 생성: {sample_file}")
                logger.info("💡 실제 크롤링 전에 샘플 파일을 수정하여 사용하세요")
                
                # 플랫폼별 파일 열기 안내
                if self.platform == 'darwin':
                    logger.info("🍎 macOS: Finder에서 파일을 열거나 Numbers/Excel로 편집하세요")
                elif self.platform == 'windows':
                    logger.info("🪟 Windows: Excel로 파일을 열어 편집하세요")
                else:
                    logger.info("🐧 Linux: LibreOffice Calc로 파일을 열어 편집하세요")
                
            except ImportError:
                logger.warning("⚠️ pandas 또는 openpyxl이 없어 샘플 파일을 생성할 수 없습니다")
                self._create_text_sample_file()
            except Exception as e:
                logger.error(f"❌ 샘플 파일 생성 중 오류: {e}")
                self._create_text_sample_file()
    
    def _create_text_sample_file(self):
        """pandas가 없을 때 텍스트 형태의 샘플 파일 생성"""
        sample_text_file = self.input_dir / "sample_format.txt"
        
        sample_content = """
웹 크롤러 입력 파일 형식 안내

Excel 파일(.xlsx)을 다음과 같은 형식으로 만들어주세요:

| 기관/단체/회사 | 주요 내용 | 웹사이트 주소 |
|---------------|----------|-------------|
| 샘플 회사 A | 회사 소개 및 주요 사업 분야 | https://example1.com |
| 샘플 기관 B | 기관 연혁 및 주요 업무 | https://example2.com |
| 샘플 단체 C | 단체 활동 현황 및 공지사항 | https://example3.com |

주의사항:
1. 첫 번째 행은 헤더입니다.
2. 각 컬럼은 위 순서대로 배치해주세요.
3. 웹사이트 주소는 http:// 또는 https://로 시작해야 합니다.
4. 파일명은 .xlsx 확장자여야 합니다.
"""
        
        try:
            with open(sample_text_file, 'w', encoding='utf-8') as f:
                f.write(sample_content)
            logger.info(f"📄 샘플 형식 안내 파일 생성: {sample_text_file}")
        except Exception as e:
            logger.error(f"❌ 샘플 안내 파일 생성 실패: {e}")
    
    def get_input_files(self):
        """input 폴더의 xlsx 파일들을 반환합니다."""
        xlsx_files = list(self.input_dir.glob("*.xlsx"))
        return [str(f) for f in xlsx_files]
    
    def get_dated_log_dir(self, date_str: str):
        """날짜별 로그 디렉토리 경로를 반환합니다."""
        log_dir = self.logs_dir / date_str
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.error(f"❌ 로그 디렉토리 생성 권한 없음: {e}")
            # 임시 디렉토리 사용
            import tempfile
            temp_log_dir = Path(tempfile.gettempdir()) / "webcrawler_logs" / date_str
            temp_log_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"⚠️ 임시 로그 디렉토리 사용: {temp_log_dir}")
            return str(temp_log_dir)
        
        return str(log_dir)
    
    def get_dated_output_dir(self, date_str: str, domain: str):
        """날짜별 출력 디렉토리 경로를 반환합니다."""
        output_dir = self.output_dir / date_str / domain
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            logger.error(f"❌ 출력 디렉토리 생성 권한 없음: {e}")
            # 임시 디렉토리 사용
            import tempfile
            temp_output_dir = Path(tempfile.gettempdir()) / "webcrawler_output" / date_str / domain
            temp_output_dir.mkdir(parents=True, exist_ok=True)
            logger.warning(f"⚠️ 임시 출력 디렉토리 사용: {temp_output_dir}")
            return str(temp_output_dir)
        
        return str(output_dir)
    
    def validate_environment(self):
        """실행 환경을 검증합니다."""
        logger.info(f"🖥️ 플랫폼: {platform.system()} {platform.release()}")
        logger.info(f"🏠 작업 디렉토리: {self.base_dir}")
        
        # 필수 디렉토리 확인
        missing_dirs = []
        for name, path in [("input", self.input_dir), ("output", self.output_dir), ("logs", self.logs_dir)]:
            if not path.exists():
                missing_dirs.append(name)
        
        if missing_dirs:
            logger.warning(f"⚠️ 누락된 폴더: {', '.join(missing_dirs)}")
            return False
        
        # 입력 파일 확인
        xlsx_files = self.get_input_files()
        if not xlsx_files:
            logger.warning("⚠️ input 폴더에 xlsx 파일이 없습니다")
            return False
        
        # 권한 확인
        if not self._check_permissions():
            return False
            
        logger.success("✅ 환경 검증 완료")
        return True
    
    def _check_permissions(self):
        """파일 시스템 권한 확인"""
        try:
            # 쓰기 권한 테스트
            test_file = self.base_dir / ".permission_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except PermissionError:
            logger.error("❌ 디렉토리 쓰기 권한이 없습니다")
            
            if self.platform == 'darwin':
                logger.info("💡 macOS 해결책:")
                logger.info("   1. 시스템 환경설정 → 보안 및 개인정보")
                logger.info("   2. 개인정보 보호 → 파일 및 폴더")
                logger.info("   3. WebCrawler에 폴더 접근 권한 부여")
            elif self.platform == 'windows':
                logger.info("💡 Windows 해결책:")
                logger.info("   1. 관리자 권한으로 실행")
                logger.info("   2. 사용자 폴더(Documents 등)에서 실행")
                
            return False
        except Exception as e:
            logger.error(f"❌ 권한 확인 중 오류: {e}")
            return False

    def print_directory_structure(self):
        """현재 디렉토리 구조를 출력합니다."""
        platform_icon = {
            'windows': '🪟',
            'darwin': '🍎', 
            'linux': '🐧'
        }.get(self.platform, '🖥️')
        
        logger.info(f"📊 {platform_icon} 현재 디렉토리 구조:")
        logger.info(f"├── {self.base_dir.name}/")
        logger.info(f"│   ├── input/     (📁 엑셀 파일 위치)")
        logger.info(f"│   ├── output/    (📁 크롤링 결과 저장)")
        logger.info(f"│   ├── logs/      (📁 실행 로그 저장)")
        logger.info(f"│   └── config/    (📁 설정 파일)")
        
        # 플랫폼별 추가 안내
        if self.platform == 'darwin':
            logger.info("💡 macOS: 폴더는 Finder에서 확인할 수 있습니다")
        elif self.platform == 'windows':
            logger.info("💡 Windows: 폴더는 파일 탐색기에서 확인할 수 있습니다")
        else:
            logger.info("💡 Linux: 폴더는 파일 매니저에서 확인할 수 있습니다")
    
    def open_directory(self, dir_type="base"):
        """플랫폼별로 디렉토리를 엽니다."""
        dir_map = {
            "base": self.base_dir,
            "input": self.input_dir,
            "output": self.output_dir,
            "logs": self.logs_dir
        }
        
        target_dir = dir_map.get(dir_type, self.base_dir)
        
        try:
            if self.platform == 'darwin':
                os.system(f'open "{target_dir}"')
            elif self.platform == 'windows':
                os.system(f'explorer "{target_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{target_dir}"')
            logger.info(f"📂 {dir_type} 폴더를 열었습니다: {target_dir}")
        except Exception as e:
            logger.error(f"❌ 폴더 열기 실패: {e}")
            logger.info(f"💡 수동으로 폴더를 여세요: {target_dir}")


def initialize_deployment_environment():
    """크로스 플랫폼 배포 환경 초기화 함수"""
    platform_name = platform.system()
    platform_icon = {
        'Windows': '🪟',
        'Darwin': '🍎',
        'Linux': '🐧'
    }.get(platform_name, '🖥️')
    
    logger.info(f"🚀 {platform_icon} {platform_name} 배포 환경 초기화 시작")
    
    path_manager = PathManager()
    
    # 1. 필요한 폴더들 생성
    path_manager.ensure_directories()
    
    # 2. 샘플 입력 파일 생성 (없을 경우에만)
    path_manager.create_sample_input_file()
    
    # 3. 디렉토리 구조 출력
    path_manager.print_directory_structure()
    
    # 4. 환경 검증
    is_valid = path_manager.validate_environment()
    
    if is_valid:
        logger.success(f"✅ {platform_name} 배포 환경 초기화 완료!")
    else:
        logger.warning("⚠️ 환경 초기화는 완료되었지만, 추가 설정이 필요합니다")
        logger.info("💡 위의 안내를 참고하여 권한 설정을 확인해주세요")
    
    return path_manager


def wait_for_user_input():
    """플랫폼별로 사용자 입력 대기"""
    platform_name = platform.system().lower()
    
    if platform_name == 'darwin':
        # macOS에서는 터미널 앱이 자동으로 닫히지 않지만, GUI 앱의 경우를 대비
        try:
            input("작업이 완료되었습니다. Enter 키를 눌러 종료...")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
    elif platform_name == 'windows':
        # Windows에서는 exe 파일 실행 시 창이 바로 닫히는 것을 방지
        if getattr(sys, 'frozen', False):
            input("작업이 완료되었습니다. Enter 키를 눌러 종료...")
    else:
        # Linux
        try:
            input("작업이 완료되었습니다. Enter 키를 눌러 종료...")
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
