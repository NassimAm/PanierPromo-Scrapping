import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import concurrent.futures
import requests
import xlsxwriter
import os

from services.formatAuchanPromotions import *
 
PATH = "web Drivers\chromedriver.exe"
driver = webdriver.Chrome(PATH)

nb_page = 0

#Changez ce paramètres selon la mémoire de votre machine
nb_max_pages = 3
 
url = "https://www.auchan.fr/boutique/promos"

magasins_ref =[
    "AUCHAN_SUPER1",
    "AUCHAN_SUPER2",
]
magasins = [
    "33800",
    "33130"
]

def get_link(link):
    ids = []
    page = requests.get(link)
    temp_soup = BeautifulSoup(page.content,"html.parser")
    features = temp_soup.find_all(class_="product-description__feature-wrapper")
    id = features[len(features)-1].find(class_="product-description__feature-values").text.replace('\n','').replace('\t','')
    
    ids.append(id)
    return ids

def checkIfSuper(name):
    return "Supermarché" in name

first = True
driver.get(url)

try :
    if first:
        myCookies = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID , 'onetrust-accept-btn-handler')))
        myCookies.click()
finally:
    for index in range(len(magasins)):
        found_magasin = False
        first = True
        start_time = time.time()
        
        try:
            if first:
                #Choosing Drive =======================================================================================================
                driver.execute_script("window.scrollTo(0, 0)") #For the button to be visible
                button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME , 'context-header__button')))
                button.click()
                try:
                    change_drive = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CLASS_NAME , 'journey-overlay-details__switch--link')))
                    change_drive.click()
                except:
                    pass
                search = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME , 'journey__search-input')))
                search.send_keys(magasins[index])
                suggestions= WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.ID , 'search_suggests')))
                elem = suggestions.find_element(By.TAG_NAME , 'li')
                elem.click()
                WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.CLASS_NAME , 'btnJourneySubmit')))
                choices = driver.find_elements(By.CLASS_NAME , 'journey-offering-context__wrapper')
                choice = None
                for i in range(len(choices)):
                    try:
                        name = choices[i].find_element(By.CLASS_NAME,'place-pos__name').text
                        if(checkIfSuper(name)):
                            choice = choices[i].find_element(By.CLASS_NAME,'btnJourneySubmit')
                            found_magasin = True
                            break
                    except:
                        pass
                
                if found_magasin:
                    choice.click()

                first = False

            if found_magasin:
                driver.implicitly_wait(3)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CLASS_NAME , 'product-price')))
                #Navigating pages =======================================================================================================
                searching = True
                sameUrl = True
                nb_page = 0
                nb_page_cpt = 1
                data = []

                while sameUrl:
                    if nb_page != 0:
                        driver.get(url+'?page='+str(nb_page+1))
                        searching = True
                    while searching:
                        try:
                            button_next = WebDriverWait(driver,5).until(EC.presence_of_element_located((By.CSS_SELECTOR,"nav.pagination-main__container a.pagination-adjacent__link i.icon-arrowRight")))
                            footer = driver.find_element(By.ID,"cms-slot-footerSlot")
                            driver.execute_script("window.scrollTo(0, {0})".format(footer.location["y"]-600))
                            if "?page=" in driver.current_url:
                                nb_page = int(driver.current_url.split('?page=',1)[1])
                            else:
                                nb_page = 1
                            if nb_page>=nb_max_pages*nb_page_cpt:
                                searching = False
                                nb_page_cpt += 1
                        except Exception as e:
                            searching = False
                            sameUrl = False
                            
                    #Iterating in products ==============================================================================================================
                    #Save the html page ==========================================
                    WebDriverWait(driver,20).until(EC.presence_of_element_located((By.CLASS_NAME , 'product-price')))
                    html = driver.page_source
                    #open the page with beautifulSoup
                    soup = BeautifulSoup(html, "html.parser")
                    items = soup.find_all(class_="list__item")
                    links = []
                    infos = []
                    #iterate in products
                    cpt = 0
                    for item in items:
                        try:
                            id_link = "https://www.auchan.fr"+item.find(class_="product-thumbnail__details-wrapper")["href"]
                            promoRef = []
                            promo = ""
                            productHeader = "vide"
                            # product-thumbnail__commercials
                            try :
                                # promoRef = item.find_all(class_='product-discount-label')
                                promoRef = []
                            finally :
                                try :
                                    promoRef += item.find_all(class_='product-discount')
                                    for onePromo in promoRef:
                                        promo += onePromo.text + " | "
                                finally:
                                    if len(promo)>=3:
                                        promo = promo[:-3]
                                    try :
                                        productHeader = item.find(class_='product-thumbnail__header').text
                                    finally:
                                        price = item.find(class_='product-price').text
                                        cpt+=1
                                        infos.append([promo, price])
                                        links.append(id_link)
                        except Exception as e:
                            pass

                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        id_product = executor.map(get_link, links)
                    id_product=list(id_product)

                    for i in range(0, len(id_product)):
                        infos[i].append(id_product[i][0])
                    data += infos
                
                fData = formatAuchanPromotions(data)

                if len(fData)>0:
                    # Save Data to Excel File ===============================================================================
                    # Create Folder if not exist
                    if not os.path.exists('Promotions/Auchan_super'):
                        os.makedirs('Promotions/Auchan_super')
                    
                    workbook = xlsxwriter.Workbook('Promotions/Auchan_super/' + magasins_ref[index] + '.xlsx')
                    worksheet = workbook.add_worksheet("Listing")

                    # Add a table to the worksheet.
                    worksheet.add_table('A1:E{0}'.format(len(fData)+1), {'data': fData,
                                                'columns': [{'header': 'CODE_BAR'},
                                                            {'header': 'PRIX'},
                                                            {'header': 'TYPE_PROMOTION'},
                                                            {'header': 'NUM_PRODUIT'},
                                                            {'header': 'REDUCTION'},
                                                            ]})
                    workbook.close()
                print((index + 1)*100/len(magasins),"%","--- %s seconds ---" % (time.time() - start_time))
            else:
                print("Aucun Supermarché Auchan pour cette adresse : " + magasins[index])
        except Exception as e:
            print(e)
            pass

driver.quit()