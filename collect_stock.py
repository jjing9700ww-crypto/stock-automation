import pandas as pd
import FinanceDataReader as fdr
from datetime import datetime

print("📊 주가 데이터 수집을 시작합니다...")

# 1. 수집하고 싶은 기업 이름과 종목 코드 지정하기
companies = {
    '삼성전자': '005930',
    'SK하이닉스': '000660',
    '현대차': '005380',
    '기아': '000270',
    '삼성중공업': '010140'
}

# 오늘 날짜 구하기 (파일 이름에 넣기 위함)
today = datetime.today().strftime('%Y-%m-%d')
filename = f'국내_주요기업_주가데이터_{today}.xlsx'

# 엑셀 파일에 여러 시트로 저장하기
with pd.ExcelWriter(filename) as writer:
    for name, code in companies.items():
        print(f"-> {name}({code}) 데이터 수집 중...")
        # 2026년 1월 1일부터의 주가 가져오기
        df = fdr.DataReader(code, '2026-01-01')
        df.to_excel(writer, sheet_name=name)

print(f"🎰 모든 데이터 수집 및 엑셀 파일({filename}) 저장 완료!")
