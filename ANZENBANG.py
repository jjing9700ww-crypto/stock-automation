import pandas as pd
import FinanceDataReader as fdr
import requests
import json
import os

print("📊 [자동매매 시스템] 20일 이평선 -5% 조건 검증을 시작합니다...")

# 깃허브 금고(Secrets)에서 안전하게 비밀 키 가져오기
APP_KEY = os.environ.get("APP_KEY")
APP_SECRET = os.environ.get("APP_SECRET")
CANO = os.environ.get("CANO")

# 1. 삼성전자 주가 수집 및 20일 이평선 계산
df = fdr.DataReader('005930', '2026-01-01')
df['이평선20'] = df['Close'].rolling(window=20).mean()

today_close = df.iloc[-1]['Close']
ma20 = df.iloc[-1]['이평선20']

# ★ 중요: 20일 이평선에서 5% 아래인 가격 계산
target_price = ma20 * 0.95  

# 2. 매수 조건 비교 (현재가 < 이평선 - 5%)
if today_close < target_price:
    print(f"🚨 매수 조건 충족! 현재가({today_close}) < 이평선-5% 가격({target_price:.0f})")
    print("🛒 한국투자증권 모의투자 API를 통해 시장가 매수 주문을 전송합니다.")
    
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
    else:
        print("❌ 증권사 API 인증 실패!")
else:
    print(f"☕ 조건 미충족. 현재가({today_close})가 매수 기준가({target_price:.0f})보다 위에 있습니다. 대기합니다.")
