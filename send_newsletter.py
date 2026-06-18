import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
import requests
from bs4 import BeautifulSoup

print("📰 [뉴스레터 시스템] 오늘의 경제 이슈 수집을 시작합니다...")

# 1. 네이버 경제 뉴스 헤드라인 크롤링 (국내/해외 경제)
url = "https://news.naver.com/section/101" # 네이버 뉴스 경제 섹션
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
res = requests.get(url, headers=headers)
soup = BeautifulSoup(res.text, 'html.parser')

# 뉴스 기사 타이틀과 링크 추출
articles = soup.select('.sa_text_title')[:10] # 상위 10개만 쏙 추출

news_html = ""
for art in articles:
    title = art.get_text().strip()
    link = art['href']
    news_html += f"""
    <li style='margin-bottom: 12px;'>
        <a href='{link}' style='color: #1a73e8; text-decoration: none; font-weight: bold;'>{title}</a>
    </li>
    """

# 2. 이메일 본문 HTML 구성 (3페이지 이내로 깔끔하게 디자인)
today_str = datetime.today().strftime('%Y년 %m월 %d일')
email_user = os.environ.get("EMAIL_USER")
email_pass = os.environ.get("EMAIL_PASS")

html_body = f"""
<html>
<body>
    <div style="max-width: 600px; margin: 0 auto; font-family: 'Malgun Gothic', sans-serif; padding: 20px; border: 1px solid #eeeeee;">
        <h2 style="color: #00c73c; border-bottom: 2px solid #00c73c; padding-bottom: 10px;">📋 {today_str} 경제 뉴스레터</h2>
        <p style="color: #666666;">안녕하세요! 오늘 아침 국내외 주요 경제 이슈 요약본입니다.</p>
        <br>
        <h3 style="color: #333333;">🔥 실시간 주요 경제 헤드라인</h3>
        <ul>
            {news_html}
        </ul>
        <br>
        <hr style="border: 0; border-top: 1px solid #eeeeee;">
        <p style="font-size: 11px; color: #999999; text-align: center;">본 메일은 GitHub Actions를 통해 매일 아침 자동으로 발송되는 나만의 비서 서비스입니다.</p>
    </div>
</body>
</html>
"""

# 3. 네이버 SMTP 서버를 이용해 내 이메일로 발송
try:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[경제 뉴스레터] {today_str} 국내외 주요 이슈"
    msg['From'] = email_user
    msg['To'] = email_user # 나에게 보내기
    
    msg.attach(MIMEText(html_body, 'html'))
    
    # 네이버 SMTP 서버 접속
    server = smtplib.SMTP_SSL('smtp.naver.com', 465)
    server.login(email_user, email_pass)
    server.sendmail(email_user, email_user, msg.as_string())
    server.quit()
    print("🚀 뉴스레터가 메일로 성공적으로 발송되었습니다!")
except Exception as e:
    print(f"❌ 메일 발송 실패: {e}")
