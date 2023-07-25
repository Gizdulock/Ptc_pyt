# -*- coding: utf-8 -*-
# Importáljuk a szükséges könyvtárakat
import sys
sys.path.append("../lib")
import requests
import json
import os
import random
from requests_html import HTMLSession # Módosított import
import time
import tqdm
import tqdm.asyncio # Importáljuk a tqdm.asyncio modult
import collections
import asyncio
import aiohttp
import logging
import requests
from bs4 import BeautifulSoup
from random import choice

# the headers to use for the requests
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}

# the function to check if a proxy works with the email and ptc websites

# Beállítjuk a naplózási szintet
logging.basicConfig(level=logging.WARNING) # Módosított sor

# Definiáljuk a változókat
ptc_url = "https://club.pokemon.com/us/pokemon-trainer-club/sign-up/" # A pokemon go ptc weboldal címe
email_url = 'https://10minutemail.net/m/?lang=en'
accounts = [] # Egy üres lista, ahol tároljuk a létrehozott fiókokat
file_name = "accounts.txt" # A fájl neve, ahol mentjük a fiókokat
proxy_limit = 5 # A maximális fiókok száma proxyként

# Definiáljuk a függvényeket

def generate_username_password():
    # Ez a függvény véletlenszerű felhasználónevet és jelszót generál
    username = "gizdu" + str(random.randint(1000, 9999)) # A felhasználónév "poke" + négy számjegy
    password = "pass" + str(random.randint(1000, 9999)) # A jelszó "pass" + négy számjegy
    return username, password

def get_temp_email():
    # Ez a függvény ideiglenes email címet kér és elmenti - Módosított függvény
    session = HTMLSession() # Létrehozunk egy HTMLSession objektumot
    response = session.get("https://10minutemail.net") # Megnyitjuk a weboldalt
    address = response.html.find("#fe_text", first=True).attrs["value"] # Kinyerjük az email címet az input mezőből
    return session, address

def download_proxy_files():
    # Ez a függvény letölti a proxy listákat a githubról és elmenti őket egy helyi mappába - Módosított függvény
    # Beolvassuk a proxy_files.json fájlt
    with open("proxy_files.json", "r") as json_file:
        data = json.load(json_file)
        # Kivesszük a proxy fájlok listáját
        proxy_files = data["proxy_files"]
    # Végigmegyünk a proxy fájlokon
    for proxy_file in proxy_files:
        # Lekérjük a proxy fájl tartalmát
        response = requests.get(proxy_file)
        # Feldaraboljuk a sorokra
        lines = response.text.split("\n")
        # Kivesszük a repo nevét és a fájl nevét a linkből
        repo_name = proxy_file.split("/")[3]
        file_name = proxy_file.split("/")[-1]
        # Ellenőrizzük, hogy létezik-e a proxy mappa, ha nem, akkor létrehozzuk
        if not os.path.exists("proxy"):
            os.mkdir("proxy")
        # Ellenőrizzük, hogy létezik-e a repo mappa a proxy mappán belül, ha nem, akkor létrehozzuk
        if not os.path.exists(os.path.join("proxy", repo_name)):
            os.mkdir(os.path.join("proxy", repo_name))
        # Elmentjük a fájl tartalmát egy helyi fájlba, amelynek neve megegyezik a fájl nevével, és amely a repo mappában van
        with open(os.path.join("proxy", repo_name, file_name), "w") as local_file:
            local_file.write(response.text)

async def get_proxy():
    # Ez a függvény választ egy véletlen proxyt az elérhető listából - Módosított függvény
    files = [] # Egy üres lista, ahova a proxy fájlok neveit gyűjtjük
    for root, dirs, filenames in os.walk("proxy"): # Végigmegyünk a proxy mappán
        for file in filenames: # Minden fájlra
            files.append(os.path.join(root, file)) # Hozzáadjuk a teljes elérési útvonalat a listához
    if files: # Ha van proxy fájl
        file_name = random.choice(files) # Választunk egy véletlen fájlt
        with open(file_name, "r") as file: # Megnyitjuk a fájlt olvasási módban
            proxies = file.read().split("\n") # Feldaraboljuk a sorokra - Módosított sor
            return proxies, file_name # Visszaadjuk az összes proxyt és a fájl nevét - Módosított sor
    else: # Ha nincs proxy fájl
        return None, None # Visszaadjuk a None értékeket - Módosított sor

def check_proxy(proxy): # proxy should be in the format 'ip:port'
    try:
        # create a proxies dictionary for requests
        proxies = {'http': 'http://' + proxy, 'https': 'https://' + proxy}
        # check if the proxy works with the email website
        response = requests.get(email_url, proxies=proxies, timeout=10, headers=headers)
        if response.status_code == 200:
            print(proxy + ' works with 10minutemail.net')
        else:
            print(proxy + ' does not work with 10minutemail.net')
            return False
        # check if the proxy works with the Pokemon Go PTC website
        response = requests.get(ptc_url, proxies=proxies, timeout=10, headers=headers)
        if response.status_code == 200:
            print(proxy + ' works with club.pokemon.com')
        else:
            print(proxy + ' does not work with club.pokemon.com')
            return False
        # if both checks passed, return True
        return True
    except requests.exceptions.RequestException as e:
        # if any error occurred, print it and return False
        print(e)
        return False


# the function to check all the proxies in a file and return a list of working ones
def check_proxies(file):
    # open the file and read the proxies
    with open(file, 'r') as f:
        proxies = f.read().splitlines()
    # create an empty list to store the working proxies
    working_proxies = []
    # loop through the proxies with a progress bar
    for proxy in tqdm(proxies):
        # check if the proxy works and append it to the list if yes
        if check_proxy(proxy):
            working_proxies.append(proxy)
    # return the list of working proxies
    return working_proxies

async def send_registration_request(username, password, address, proxies):
    # Ez a függvény elküldi a regisztrációs kérést a ptc weboldalnak - Módosított függvény
    data = { # A kérésben küldött adatok
        "csrfmiddlewaretoken": "null",
        "dob": "1990-01-01",
        "country": "US",
        "screen_name": username,
        "password": password,
        "confirm_password": password,
        "email": address,
        "confirm_email": address,
        "public_profile_opt_in": "False",
        "terms": "on"
    }
    headers = { # A kérésben küldött fejlécek
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:95.0) Gecko/20100101 Firefox/95.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://club.pokemon.com",
        "DNT": "1",
        "Connection": "keep-alive",
        "Referer": ptc_url,
    }
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), timeout=aiohttp.ClientTimeout(total=20)) as session: # Létrehozunk egy aszinkron HTTP klienst - Módosított sor
        response = await session.post(ptc_url, data=data, headers=headers, proxy=f"http://{proxies['http']}") # Elküldjük az aszinkron kérést
    return response

def check_email_account(session):
    # Ez a függvény ellenőrzi az email fiókot és megkeresi az aktiváló linket - Módosított függvény
    response = session.get("https://10minutemail.net/mailbox.ajax.php?time=" + str(int(time.time()))) # Lekérjük az email üzeneteket
    messages = response.json() # Feldolgozzuk az üzeneteket JSON formátumban
    for message in messages:
        if message["mail_from"] == "noreply@pokemon.com": # Ha az üzenet a pokemon.com-tól jött
            link = message["mail_body"].split("href=")[1].split(">")[0].strip('"') # Kinyerjük az aktiváló linket az html kódból
            return link

async def open_activation_link(link, proxies):
    # Ez a függvény megnyitja az aktiváló linket és visszaigazolja a fiókot - Módosított függvény
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False), timeout=aiohttp.ClientTimeout(total=20)) as session: # Létrehozunk egy aszinkron HTTP klienst - Módosított sor
        response = await session.get(link, proxy=f"http://{proxies['http']}") # Megnyitjuk az aszinkron kérést
    return response

def save_account_to_file(username, password):
    # Ez a függvény elmenti a sikeresen regisztrált és aktivált fiókot egy fájlba
    with open(file_name, "a") as file: # Megnyitjuk a fájlt írási módban
        file.write(f"{username},{password}\n") # Hozzáírjuk a fiók adatait a következő sorba

async def wrapper (_async_func, _interval):
  while True:
    await _async_func() # Itt kell beilleszteni
    await asyncio.sleep (_interval)

total_proxies = 0 # Létrehozunk egy változót az összes proxy számolására - Új sor
n_accounts = 10 # Létrehozunk egy változót az elkészítendő fiókok számára - Új sor
async def main():
    # Ez a fő függvény, ami meghívja az előző függvényeket egy ciklusban annyiszor, ahány fiókot szeretnénk létrehozni - Módosított függvény
    global total_proxies # Globális változónak jelöljük - Új sor
    start_time = time.time() # Elmentjük az indulási időt
    proxy_counter = collections.Counter() # Létrehozunk egy számlálót a proxyk használatára
    tasks = [get_proxy for _ in range(n_accounts)]
    while True: # Új sor: kezdődik a ciklus
        try: # Új sor: kezdődik a try blokk
            for result in tqdm.asyncio.tqdm.as_completed([task() for task in tasks]): # Létrehozunk egy folyamatjelzőt az as_completed metódussal
                proxy, file_name = await result # Megvárjuk a proxy és a fájl nevét - Módosított sor
                if not total_proxies and file_name: # Ha még nem számoltuk meg az összes proxyt és van fájl név - Új feltétel
                    with open(file_name, "r+") as file: # Megnyitjuk a fájlt olvasásra és írásra - Módosított sor
                        total_proxies = len(file.read().split("\n")) # Megszámoljuk az összes proxyt - Új sor
                        tqdm.asyncio.tqdm.set_description(tqdm.asyncio.tqdm(range(total_proxies), total=total_proxies), f"Total proxies: {total_proxies}")
                if not proxies: # Ha nincs jó proxy - Új feltétel
                    logging.warning(f"No good proxy in {file_name}")
                continue # Folytatjuk a ciklust
                proxy = random.choice(proxies) # Választunk egy véletlen proxyt - Új sor
                proxies = {'http': 'http://' + proxy, 'https': 'https://' + proxy} # Létrehozzuk a proxies szótárt - Új sor
                proxy_counter.update([proxy]) # Növeljük a számlálót a proxyval
                if proxy_counter[proxy] > proxy_limit: # Ha elérte a limitet a proxy
                    logging.warning(f"Proxy limit reached: {proxy}")
                    continue # Folytatjuk a ciklust - Módosított sor
                registration_response = requests.post(registration_url, data=payload, proxies=proxies) # Elküldjük a regisztrációs kérést - Módosított sor
                if registration_response.status_code == 200: # Ha a kérés sikeres volt
                    logging.info(f"Registration successful for {username}")
                    activation_link = check_email_account(session) # Ellenőrizzük az email fiókot
                    if activation_link: # Ha találtunk aktiváló linket
                        activation_response = requests.get(activation_link, proxies=proxies) # Megnyitjuk az aktiváló linket - Módosított sor
                        if activation_response.status_code == 200: # Ha a kérés sikeres volt
                            logging.info(f"Activation successful for {username}")
                            accounts.append((username, password, address)) # Hozzáadjuk a fiókot a listához
                            save_account_to_file(username, password) # Elmentjük a fiókot a fájlba
                        else: # Ha a kérés sikertelen volt
                            logging.warning(f"Activation failed for {username}")
                    else: # Ha nem találtunk aktiváló linket
                        logging.warning(f"No activation link found for {username}")
                else: # Ha a kérés sikertelen volt
                    logging.warning(f"Registration failed for {username}")
            break # Új sor: kilépünk a ciklusból, ha nincs több hiba
        except Exception as e: # Új sor: kezdődik az except blokk
            print(e) # Kiírjuk a hibát
            time.sleep(3600) # Várunk egy órát
            continue # Folytatjuk a ciklust - Módosított sor

# Meghívjuk a download_proxy_files() függvényt
download_proxy_files()

# Meghívjuk a main() függvényt
asyncio.run(main())

