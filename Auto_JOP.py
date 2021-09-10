from datetime import datetime
from selenium import webdriver
from haversine import haversine
from folium.features import DivIcon
from email.mime.text import MIMEText
import requests
import json
import time
import googlemaps
import folium
import polyline
import os
import boto3
import smtplib
from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys

# day
year = datetime.now().year
month = datetime.now().month
day = datetime.now().day

# Saramin API
key = "엑세스 키값" 
loc_cd = "101000+102180" # 지역코드
published = str(year) + "-" + str(month) + "-" + str(day) # 등록일 yyyy-mm-dd

# headless 옵션
options = webdriver.ChromeOptions()
options.add_argument('headless')
options.add_argument('window-size=1920x1080')
options.add_argument("disable-gpu")

# Google Maps
gmaps_key = "Google Maps API 키값"
gmaps = googlemaps.Client(key=gmaps_key)
home = '집 위치'

# 사람인 API를 통해 적용된 필터에 맞는 공고 데이터 수집
def Saramin(keyword):
    URL = "https://oapi.saramin.co.kr/job-search?access-key=%s&keywords=%s&loc_cd=%s&published=%s&count=110&fields=count" % (key,keyword, loc_cd, published)
    
    # API를 통해 Json 형태로 데이터 추출
    response = requests.get(URL)
    data = response.json()

    # 데이터 전처리
    new_data = []
    for i in range(len(data['jobs']['job'])):
        if data['jobs']['job'][i]['position']['experience-level']['code'] != 2: # 신입(0), 경력무관(1), 경력(2)
            new_data.append(data['jobs']['job'][i])

    # 원하는 요소를 전처리  추출
    company = [] # 회사명
    title = [] # 공고명
    location = [] # 회사 위치
    expiration_date = [] # 공고 마감일
    com_url = [] # 공고 URL
    apply_cnt = [] # 현재 지원자수
    for i in range(len(new_data)):
        com_url.append(new_data[i]['url'])
        company.append(new_data[i]["company"]["detail"]["name"].replace("(주)", ""))
        title.append(new_data[i]["position"]["title"])
        loc = new_data[i]["position"]["location"]["name"].split(" &gt; ")
        loc_res = (loc[0] + " " + loc[1])
        location.append(loc_res)
        dt_FromTs = new_data[i]['expiration-timestamp']
        expiration_date.append(str(datetime.fromtimestamp(int(dt_FromTs))))
        apply_cnt.append(new_data[i]['apply-cnt'])

    # 2차원 리스트로 변환
    com_list = []
    for i in range(len(company)):
        com_list.insert(i, [company[i], title[i], location[i], expiration_date[i], com_url[i], apply_cnt[i]])

    return com_list

def Job_Planet(a): # planet_com / [회사1, 회사2, 회사3, ...]
    # webdriver 접속
    driver = webdriver.Chrome('chromedriver', chrome_options=options) # headless 적용
    driver.get("https://www.jobplanet.co.kr/")
    driver.maximize_window()
    driver.implicitly_wait(5)

    # 로그인 버튼 클릭
    login_link = driver.find_element_by_css_selector('a.btn_txt.login')
    login_link.click()
    driver.implicitly_wait(5)

    # 페이스북으로 로그인
    fb_link = driver.find_element_by_css_selector('#signInSignInCon > div.signInsignIn_wrap > div > section.section_facebook > a')
    fb_link.click()
    driver.implicitly_wait(5)

    # id 입력
    username_input = driver.find_element_by_css_selector('#email')
    username_input.send_keys("페이스북 ID")

    # password 입력
    password_input = driver.find_element_by_css_selector('#pass')
    password_input.send_keys("페이스북 비밀번호") 
    driver.find_element_by_css_selector('#loginbutton').click()
    driver.implicitly_wait(5)

    # 회사명 검색
    for i in range(len(a)):
        driver.get("https://www.jobplanet.co.kr/")
        driver.implicitly_wait(5)
        driver.get("https://www.jobplanet.co.kr/companies/cover")
        driver.implicitly_wait(5)
        search_com = driver.find_element_by_css_selector('#search_bar_search_query')
        search_com.send_keys(a[i])
        driver.find_element_by_css_selector('#search_form > div > button').click()
        driver.implicitly_wait(5)

        # 예외 처리
        try:
            driver.find_element_by_css_selector('#mainContents > div:nth-child(1) > div > div.result_company_card > div.is_company_card > div > a').click()
            driver.implicitly_wait(5)

            # 점수
            score = driver.find_element_by_css_selector('body > div.body_wrap > div.cmp_hd > div.new_top_bnr > div > div.top_bnr_wrap > div > div > div.company_info_sec > div.company_info_box > div.about_company > div.score_area.type_total_year > div > span').text
            
            # 후기
            dg = driver.page_source
            soup = BeautifulSoup(dg, 'html.parser')
            comment_raw = soup.find_all("h2", {"class" : "us_label"})
            comments = [comment.text for comment in comment_raw]
            for j in range(len(comments)):
                comments[j] = comments[j].replace("\nBEST\n      \"", "")
                comments[j] = comments[j].replace("\n", " ")
                comments[j] = comments[j].replace("\"     ", "")

            company[i].append(score)
            if len(comments) != 0:
                company[i].append(comments)
            else:
                company[i].append([])
                
        except: # 회사가 목록에 존재하지 않을경우
            company[i].append('없음') # 평점 없음 
            company[i].append([]) # 후기 빈 리스트
    
    return driver

# 입력한 위치의 위도, 경도를 출력
def val_lat_lng(loc):
    user_info = gmaps.geocode(loc, language = 'ko')
    user_geo = user_info[0].get('geometry')
    user_lat = user_geo['location']['lat'] # 위도
    user_lng = user_geo['location']['lng'] # 경도
    loc_val = [user_lat, user_lng]
    
    return loc_val

def loc_map(com):
    loc_com = val_lat_lng(com) # 회사 위도 & 경도
    loc_center = [round((loc_com[0] + loc_home[0])/2, 7), round((loc_com[1] + loc_home[1])/2, 7)]
    
    # 길찾기
    directions_result = gmaps.directions(home, com, mode = "transit")
    
    # 집과 회사의 거리차에 따른 지도의 zoom 조절
    hc_distance = round(haversine(loc_home, loc_com), 2)
    if hc_distance < 6:
        zoom_start = 14
    elif hc_distance >= 6 and hc_distance < 12:
        zoom_start = 13
    elif hc_distance >= 12 and hc_distance < 24:
        zoom_start = 12
    elif hc_distance >= 24 and hc_distance < 48:
        zoom_start = 11
    else:
        zoom_start = 10

    g_map = folium.Map(location = loc_center, zoom_start = zoom_start)
    duration = directions_result[0]['legs'][0]['duration']['text'].replace(" hours", "시간").replace(" hour", "시간").replace(" mins", "분") # 소요 시간
    distance = directions_result[0]['legs'][0]['distance']['text'].replace(" km", "km") # 거리

    # Polyline Decode
    for i in range(len(directions_result[0]['legs'][0]['steps'])):
        a = directions_result[0]['legs'][0]['steps'][i]
        b = polyline.decode(a['polyline']['points'])
        folium.PolyLine(b, color="red", weight=8, opacity=1).add_to(g_map)

    folium.Marker(
        location = (directions_result[0]['legs'][0]['start_location']['lat'], directions_result[0]['legs'][0]['start_location']['lng']),
        popup = 'Home',
        icon = folium.Icon(color='blue',icon='star')    
    ).add_to(g_map)

    folium.Marker(
        location = (directions_result[0]['legs'][0]['end_location']['lat'], directions_result[0]['legs'][0]['end_location']['lng']),
        tooltip = 'company',
        popup = '''
            Company
            Duration : %s
            Distance : %s
        ''' % (directions_result[0]['legs'][0]['duration']['text'], directions_result[0]['legs'][0]['distance']['text']),
        icon = folium.Icon(color='blue',icon='star')
    ).add_to(g_map)

    html = '''
    <div style="font-size: 24pt">Distance : {a}</div>
    <div style="font-size: 24pt">Duration : {b}</div>
    '''.format(a=distance, b = duration)

    folium.Marker(
        location = loc_center,
        icon = DivIcon(
            icon_size=(600,36),
            icon_anchor=(0,0),
            html = html,
        )
    ).add_to(g_map)
    
    return g_map

# 지도 html을 이미지 파일로 생성
def make_png(g_map):
    delay = 5
    fn = 'map.html'
    tmpurl='file://{path}/{mapfile}'.format(path=os.getcwd(),mapfile=fn)
    g_map.save(fn)

    browser = webdriver.Chrome('chromedriver', chrome_options=options) # headless 적용
    browser.get(tmpurl)

    time.sleep(delay)
    browser.save_screenshot('{day}_{com}.png'.format(day = published, com = com)) # YYYY-MM-DD_회사명.png
    browser.quit()
    
# 생성한 이미지 파일을 AWS S3에 업로드
def to_s3(i, com):
    bucket_name = '버켓명'
    image_name = '{day}_{com}.png'.format(day = published, com = com)
    s3_image = '{day}/{name}.png'.format(day = published, name = com)
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    bucket.upload_file(
        image_name, s3_image, ExtraArgs = {'ContentType' : 'image/png'})

    s3_url = "버켓 이미지 파일 주소"
    company[i].append(s3_url)
    
# E-Mail에 첨부할 텍스트 양식 전처리
def extract_mail(company):
    list_num = ['①', '②', '③', '④', '⑤']
    mail_text = []
    for i in range(len(company)):
        mail_text.append('회    사 : {com}'.format(com = company[i][0]))
        mail_text.append('공 고 명 : {com}'.format(com = company[i][1]))
        mail_text.append('위    치 : {com}'.format(com = company[i][2]))
        mail_text.append('지 원 자 : {com}명'.format(com = company[i][5]))
        mail_text.append('마 감 일 : {com}'.format(com = company[i][3]))
        mail_text.append('평    점 : {com}'.format(com = company[i][6]))
        mail_text.append('공    고 : {com}'.format(com = company[i][4]))
        mail_text.append('지    도 : {com}'.format(com = company[i][8]))
        if len(company[i][7]) == 0:
            mail_text.append('후    기 : {com}'.format(com = "없음"))
        else:
            mail_text.append('후    기 :')
            for j in range(len(company[i][7])):
                mail_text.append('{num} {com}'.format(num = list_num[j], com = company[i][7][j]))
        mail_text.append(' ')

    mail_text = "\n".join(mail_text) + "\n"
    return mail_text

def send_Mail(mail_text):
    sendEmail = "착신 메일주소" 
    recvEmail = "수신 메일주소" 
    password = "메일 패스워드" 

    smtpName = "smtp.gmail.com" #smtp 서버 주소
    smtpPort = 587 #smtp 포트 번호

    msg = MIMEText(mail_text)
    
    msg['Subject'] = published + " 공고"
    msg['From'] = sendEmail
    msg['To'] = recvEmail

    s = smtplib.SMTP(smtpName , smtpPort) # 메일 서버 연결
    s.starttls() # TLS 보안 처리
    s.login(sendEmail, password) # 로그인
    s.sendmail(sendEmail, recvEmail, msg.as_string() ) # 문자열로 변환 후 메일 전송
    s.close() #smtp 서버 연결 종료

# 서버에 남아 있는 이미지 파일 제거
def removeExtensionFile(filePath, fileExtension):
    if os.path.exists(filePath):
        for file in os.scandir(filePath):
            if file.name.endswith(fileExtension):
                os.remove(file.path)
        return 'Remove File :' + fileExtension
    else:
        return 'Directory Not Found'
