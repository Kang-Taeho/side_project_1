import pymysql
from bs4 import BeautifulSoup
import time

from selenium import webdriver

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


#문피아 선독점 (판타지, 새작품순)
URL = 'https://novel.munpia.com/page/hd.platinum/group/pl.serial/exclusive/true/view/allend'

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches",["enable-logging"])
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
driver.get(url=URL)

WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div[1]/div/section/section[1]/ul/li[3]/a"))).click()
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div[1]/div/section/section[2]/ul[1]/li[4]"))).click()
time.sleep(2)
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div[1]/div/section/section[3]/div[1]/a"))).click()
WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[1]/div[1]/div/section/section[3]/nav/ul/li[3]"))).click()
time.sleep(2)

page_index = 0
novel_Id_Name_List = []

#연재작 Id,Name 저장
while True :
    if page_index != 6 : page_index += 1 

    try : 
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="NOVELOUS-CONTENTS"]/section[4]/ul/li[{0}]'.format(page_index)))).click()
        time.sleep(1)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source,'html.parser')

        novels = soup.select_one('#SECTION-LIST > ul')
        novel_infos = novels.find_all('a',{'class' : 'title col-xs-6'})
        for novel_info in novel_infos :
            novel_Id = novel_info['href']
            novel_Id = novel_Id[ novel_Id.rfind('/')+1 : ]
            novel_Name = novel_info['title']
            novel_Id_Name_List.append((int(novel_Id),novel_Name))
    except Exception :
        break

#완결작 Id,Name 저장
WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="SECTION-MENU"]/ul/li[2]/a'))).click()
time.sleep(1)

page_index = 0
while True :
    if page_index != 6 : page_index += 1 

    try : 
        WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="NOVELOUS-CONTENTS"]/section[4]/ul/li[{0}]'.format(page_index)))).click()
        time.sleep(1)

        page_source = driver.page_source
        soup = BeautifulSoup(page_source,'html.parser')

        novels = soup.select_one('#SECTION-LIST > ul')
        novel_infos = novels.find_all('a',{'class' : 'title col-xs-6'})
        for novel_info in novel_infos :
            novel_Id = novel_info['href']
            novel_Id = novel_Id[ novel_Id.rfind('/')+1 : ]
            novel_Name = novel_info['title']
            novel_Id_Name_List.append((int(novel_Id),novel_Name))
    except Exception :
        break

#db 저장
db = pymysql.connect(host='127.0.0.1',port=3306,user='root',passwd='trigger3587!',db='product',charset='utf8')
try:
    with db.cursor() as cursor :
        sql = "SELECT id FROM munpia_product"
        cursor.execute(sql)
        db_novel = cursor.fetchall()

        for novel_Id, novel_Name in novel_Id_Name_List :
            URL = 'https://novel.munpia.com/' + str(novel_Id)
            driver.get(url=URL)

            page_source = driver.page_source
            soup = BeautifulSoup(page_source,'html.parser')

            novel_Visitor = soup.find('dl',{'class' : 'meta-etc meta','style' : 'letter-spacing:-0.2px;padding-bottom: 10px;'}).get_text().replace('\n','')
            novel_Visitor = novel_Visitor[novel_Visitor.find('조회수 :')+5 : novel_Visitor.find('추천수')].replace(',','')

            if (novel_Id,) in db_novel :
                print("포함")
                sql = """UPDATE munpia_product
                            SET visitor=%s
                            WHERE id=%s"""
                val = (novel_Visitor,novel_Id)
            else :
                novel_Category = soup.find('strong').get_text().replace(' ','')

                novel_Author = soup.find('dl',{'class' : 'meta-author meta'}).get_text().replace('글','').replace('\n','')
                if '아카데미 작가' in novel_Author :
                    novel_Author = novel_Author[:novel_Author.find('아카데미 작가')]
                elif '그림/삽화' in novel_Author :
                    novel_Author = novel_Author[:novel_Author.find('그림/삽화')]

                novel_Visitor = soup.find('dl',{'class' : 'meta-etc meta','style' : 'letter-spacing:-0.2px;padding-bottom: 10px;'}).get_text().replace('\n','')
                novel_Visitor = novel_Visitor[novel_Visitor.find('조회수 :')+5 : novel_Visitor.find('추천수')].replace(',','')

                novel_Content = soup.find('p',{'class' : 'story'}).get_text().replace('\n','')

                novel_Keyword = soup.find('div',{'class' : 'tag-list expand'})
                if novel_Keyword is not None :
                    novel_Keyword = novel_Keyword.get_text().replace('\n','')

                sql = """INSERT INTO munpia_product(id,title,author,category,visitor,keyword,content)
                                    VALUES (%s,%s,%s,%s,%s,%s,%s)"""
                val = (novel_Id,novel_Name,novel_Author,novel_Category,novel_Visitor,novel_Keyword,novel_Content)
            cursor.execute(sql,val)
            db.commit()
finally :
    db.close()

