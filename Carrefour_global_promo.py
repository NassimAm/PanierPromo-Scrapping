from time import sleep
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import xlsxwriter
import os
import math

from services.formatCarrefourPromotions import *

def chunks(l, n):
    """Yield n number of striped chunks from l."""
    for i in range(0, n):
        yield l[i::n]

def getArticleInfo(art):
    try:
        item = art.find_element(By.CLASS_NAME, 'ds-product-card-refonte')
        id = item.get_attribute("id")
        image = item.find_element(By.TAG_NAME,"img").get_attribute("data-src")
        name = item.find_element(By.CLASS_NAME , 'ds-title')
        price = item.find_element(By.CLASS_NAME , 'product-price__amount-value')
        return [id,image,name.text,price.text]
    except:
        return []

def checkIfMarket(name):
    return "Market" in name

PATH = "Web Drivers\chromedriver.exe"

driver = webdriver.Chrome(PATH)
driver.maximize_window()

url = "https://www.carrefour.fr/"

#Set to -1 to make it unlimited ==========================================
nb_max_pages = 5

driver.get(url)

try :
    myCookies = WebDriverWait(driver, 40).until(EC.presence_of_element_located((By.ID , 'onetrust-reject-all-handler')))
    myCookies.click()
    rayonsButton = WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.CLASS_NAME , 'mainbar__nav-toggle-icon')))
    rayonsButton.click()
    promotionsButton = WebDriverWait(driver, 40).until(EC.element_to_be_clickable((By.CLASS_NAME , 'nav-item__link--promotion')))
    promotionsButton.click()
    
    driver.get(url + 'promotions?filters%5Bproduct.categories.name%5D%5B0%5D=Boissons&filters%5Bproduct.categories.name%5D%5B1%5D=Entretien%20et%20Nettoyage&filters%5Bproduct.categories.name%5D%5B2%5D=Epicerie%20sal%C3%A9e&filters%5Bproduct.categories.name%5D%5B3%5D=Epicerie%20sucr%C3%A9e&filters%5Bproduct.categories.name%5D%5B4%5D=Frais&filters%5Bproduct.categories.name%5D%5B5%5D=Fruits%20et%20L%C3%A9gumes&filters%5Bproduct.categories.name%5D%5B6%5D=Hygi%C3%A8ne%20et%20Beaut%C3%A9&filters%5Bproduct.categories.name%5D%5B7%5D=Pains%20et%20P%C3%A2tisseries&filters%5Bproduct.categories.name%5D%5B8%5D=Surgel%C3%A9s&filters%5Bproduct.categories.name%5D%5B9%5D=Viandes%20et%20Poissons&noRedirect=0')

finally:
    nb_page_cpt = 1
    start = time.time()

    # ------------------------------ Nombre de pages ----------------------------------
    WebDriverWait(driver,60).until(EC.presence_of_element_located((By.CLASS_NAME , 'search-results-count--promotion')))
    promonb = driver.find_element(By.CLASS_NAME,"search-results-count--promotion").text
    NBpromoPage = math.ceil(int(promonb.split()[0])/30)
    # -----------------------------------------------------------------------------------
    searching = True
    sameUrl = True
    nb_page = 0
    data = []
    while sameUrl:
        if nb_page != 0:
            if(nb_page <= NBpromoPage):
                driver.refresh()
                searching = True
            else:
                searching = False
                sameUrl = False
        while searching:
            try:
                footer = driver.find_element(By.ID,"colophon")
                driver.execute_script("window.scrollTo(0, {0})".format(footer.location["y"]-600))
                if "page=" in driver.current_url:
                    nb_page = int(driver.current_url.split('page=',1)[1])
                else:
                    nb_page = 1

                if(( nb_page >= nb_max_pages*nb_page_cpt) or (nb_page >= NBpromoPage)):
                    searching = False
                    nb_page += 1
                    nb_page_cpt += 1

            except Exception as e:
                searching = False
                sameUrl = False
                
        #Save the html page ==========================================
        WebDriverWait(driver,20).until(EC.presence_of_element_located((By.CLASS_NAME , 'product-price__amounts')))
        html = driver.page_source
        #open the page with beautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        items = soup.find_all(class_="product-grid-item")
        #iterate in products
        for item in items:
            try:
                promoRef = []
                promo = ""
                # product-thumbnail__commercials
                try :
                    promoRef = item.find_all(class_='promotion-description__labels')
                finally :
                    try :
                        for onePromo in promoRef:
                            promo += onePromo.text + " | "
                    finally:
                        price = item.find(class_='product-price__amount-value').text
                        code = item.find(class_='ds-product-card-refonte')["id"]
                        data.append([code, promo, price])
            except:
                continue
        
        
    fData = formatCarrefourPromotions(data)
    #Save Data to Excel File ==================================================-=============================
    #Create Folder if not exist
    
    if not os.path.exists('Promotions/Carrefour'):
        os.makedirs('Promotions/Carrefour')
    
    workbook = xlsxwriter.Workbook('Promotions/Carrefour/Carrefour.xlsx')
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
    
    print("Time : --- %s seconds ---" % (time.time() - start))

driver.quit()