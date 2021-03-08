# Toy Project - 구직 공고 수신 자동화
## 개발환경
- Programming Language : Python
- IDLE : Jupyter Notebook
- AWS : S3, EC2

## 개발내역
01. 사람인 API를 통한 공고 데이터 수집
02. Selenium을 사용하여 잡플래닛에서 해당 회사에 대한 평점 및 후기 크롤링
03. googlemaps API를 사용하여 해당 회사에서 집까지의 거리 및 경로 데이터 수집
04. 수집한 경로 데이터를 구글 지도에 표시 및 이미지 파일의 형태로 변환
05. 변환한 지도 이미지 파일을 S3에 public 권한으로 저장
06. 기존에 수집한 데이터를 원하는 형태로 전처리
07. 전처리한 데이터를 구글 → 네이버로 메일 전송
08. 프로토타입 1차적으로 구현
09. 권한 확인 인터페이스가 새로 생성되어 코드 추가  
10. 9에서 생성한 코드가 구글 웹드라이버 Headless 옵션에서 실행이 되지 않는 현상 발생  
11. driver 처음 실행 시 stale element reference: element is not attached to the page document 오류 발생  
12. AWS Lambda의 Layers에 파이썬 모듈 등록
13. 평점 크롤링 부분 수정 210209
14. 텔레그램 봇 연동 후 메시지 전송 및 수신 부분까지 구현 210308

## 진행중인 내역
01. 지도 이미지 링크 개선
02. 잡플래닛 크롤링 과정 중 검색 버튼의 selecter를 찾지 못하는 오류(해결)
~~~
driver.find_element_by_css_selector('#search_form > div > div > button').click()
~~~
~~~
driver.find_element_by_css_selector('#search_form > div > div > button').send_keys(Keys.ENTER)
~~~
03. AWS Lambda와 Folium 연동
> folium을 통해 출력된 지도 이미지 파일을 s3에 저장  

## 향후 계획
01. 이메일 링크 주소 생성 코드부분 수정  
02. AWS Lambda와 AWS SES 연동을 통한 메일 송신  
03. AWS Lambda를 대체하여 EC2 서버에 구현
04. 메일 전송에서 텔레그램 봇의 형태로 변경 고려
