import pandas as pd
import FinanceDataReader as fdr
import requests
import json
import os
from datetime import datetime

print("📊 [실시간 감시 시스템] 조건 검증 및 한도 체크를 시작합니다...")

# ================= 설정 구간 =================
LIMIT_PER_DAY = 500000  # 💰 하루 최대 매수 한도 (예: 50만 원)
LOG_FILE = "trade_log.txt"
# ============================================

# 오늘 날짜 구하기
today = datetime.today().strftime('%Y-%m-%d')

# 1. 오늘 이미 한도를 채웠는지 확인하기 (로그 파일 읽기)
today_total_spent = 0
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith(today):
                # 로그 파일에서 오늘 날짜 뒤에 적힌 금액을 찾아 더합니다.
                today_total_spent = int(line.split(",")[1].strip())

print(f"💸 오늘 현재까지 누적 매수 금액: {today_total_spent:,}원 (최대 한도: {LIMIT_PER_DAY:,}원)")

if today_total_spent >= LIMIT_PER_DAY:
    print("🛑 [알림] 오늘 지정한 최대 투자 금액을 모두 사용했습니다. 감시를 종료합니다.")
    exit() # 프로그램 강제 종료 (주문 안 함)

# 깃허브 금고(Secrets)에서 안전하게 비밀 키 가져오기
APP_KEY = os.environ.get("APP_KEY")
APP_SECRET = os.environ.get("APP_SECRET")
CANO = os.environ.get("CANO")

# 2. 삼성전자 현재 주가 수집 및 20일 이평선 계산
df = fdr.DataReader('005930', '2026-01-01')
df['이평선20'] = df['Close'].rolling(window=20).mean()

today_close = df.iloc[-1]['Close']
ma20 = df.iloc[-1]['이평선20']

# 20일 이평선에서 5% 아래인 가격 계산
target_price = ma20 * 0.95  

# 3. 매수 조건 비교 (현재가 < 이평선 - 5%)
if today_close < target_price:
    print(f"🚨 매수 조건 충족! 현재가({today_close:,}원) < 매수 기준가({target_price:.0f}원)")
    
    # 4. 이번 주문을 넣었을 때 한도를 넘지 않는지 최종 체크
    if today_total_spent + today_close > LIMIT_PER_DAY:
        print(f"⚠️ 이번에 1주를 더 사면 하루 한도({LIMIT_PER_DAY:,}원)를 초과하게 됩니다. 주문을 취소합니다.")
        exit()

    # [인증] 증권사 접근 토큰(Access Token) 발급 신청
    auth_url = "https://vtsopenapi.koreainvestment.com:29443/oauth2/tokenP"
    headers = {"content-type": "application/json"}
    body = {"grant_type": "client_credentials", "appkey": APP_KEY, "secretkey": APP_SECRET}
    
    res = requests.post(auth_url, headers=headers, data=json.dumps(body))
    access_token = res.json().get('access_token')
    
    if access_token:
        # [주문] 삼성전자 1주 시장가 현금 매수 주문
        order_url = "https://vtsopenapi.koreainvestment.com:29443/uapi/domestic-stock/v1/trading/order-cash"
        
        order_headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {access_token}",
            "appkey": APP_KEY,
            "appsecret": APP_SECRET,
            "tr_id": "VTTC0802U"
        }
        
        order_body = {
            "CANO": CANO,
            "ACNT_PRDT_CD": "01",
            "PDNO": "005930",
            "ORD_DVSN": "01",
            "ORD_QTY": "1",
            "ORD_UNPR": "0"
        }
        
        order_res = requests.post(order_url, headers=order_headers, data=json.dumps(order_body))
        res_json = order_res.json()
        print(f"📡 주문 전송 결과: [{res_json.get('rt_cd')}] {res_json.get('msg1')}")
        
        # 5. 주문이 성공했다면 로그 파일에 오늘 쓴 금액 업데이트 기록 남기기
        if res_json.get('rt_cd') == '0':
            new_total = today_total_spent + today_close
            with open(LOG_FILE, "a") as f:
                f.write(f"{today}, {int(new_total)}\n")
            print(f"📝 매수 기록 완료! 오늘 누적 금액이 {new_total:,}원으로 업데이트되었습니다.")
            
    else:
        print("❌ 증권사 API 인증 실패!")
else:
    print(f"☕ 조건 미충족. 현재가({today_close:,}원)가 매수 기준가({target_price:.0f}원) 위에 있습니다. 대기합니다.")
