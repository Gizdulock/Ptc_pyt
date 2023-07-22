# Importáljuk a szükséges könyvtárakat
import requests
import random
import tempmail
import proxyscrape
import time
import tqdm
import collections

# Definiáljuk a változókat
ptc_url = "https://club.pokemon.com/us/pokemon-trainer-club/sign-up/" # A pokemon go ptc weboldal címe
proxy_collector = proxyscrape.create_collector('default', 'https') # Létrehozunk egy proxy gyűjtőt
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
    # Ez a függvény ideiglenes email címet kér és elmenti
    email = tempmail.TempMail() # Létrehozunk egy email objektumot
    address = email.get_email_address() # Lekérjük az email címet
    return email, address

def get_proxy():
    # Ez a függvény proxyt választ és beállítja a webes kéréshez
    proxy = proxy_collector.get_proxy() # Lekérünk egy proxyt a gyűjtőből
    proxies = {
        "http": f"http://{proxy.host}:{proxy.port}",
        "https": f"https://{proxy.host}:{proxy.port}"
    } # Létrehozunk egy proxy szótárat
    return proxies

def check_proxy(proxy):
    # Ez a függvény ellenőrzi, hogy a proxy elérhető-e a pokemon go ptc weboldalával és az email szolgáltatóval
    try:
        response_ptc = requests.get(ptc_url, proxies=proxy, timeout=10) # Megpróbáljuk elérni a pokemon go ptc weboldalát a proxyval
        response_email = tempmail.check_email_domain(proxy) # Megpróbáljuk elérni az email szolgáltatót a proxyval
        if response_ptc.status_code == 200 and response_email: # Ha mindkét kérés sikeres volt
            return True # Visszaadjuk, hogy a proxy jó
        else: # Ha valamelyik kérés sikertelen volt
            return False # Visszaadjuk, hogy a proxy rossz
    except: # Ha bármilyen hiba történt
        return False # Visszaadjuk, hogy a proxy rossz

def send_registration_request(username, password, address, proxies):
    # Ez a függvény elküldi a regisztrációs kérést a pokemon go ptc weboldalának
    data = {
        "username": username,
        "password": password,
        "confirm_password": password,
        "email": address,
        "confirm_email": address,
        "public_profile_opt_in": "False",
        "screen_name": username,
        "terms": "on"
    } # Létrehozunk egy adat szótárat a regisztrációs űrlap kitöltéséhez
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    } # Létrehozunk egy fejléc szótárat az álcázás érdekében
    response = requests.post(ptc_url, data=data, headers=headers, proxies=proxies) # Elküldjük a kérést
    return response

def check_email_account(email):
    # Ez a függvény ellenőrzi az email fiókot és megkeresi az aktiváló linket
    messages = email.get_messages() # Lekérjük az email üzeneteket
    for message in messages:
        if message["sender"] == "noreply@pokemon.com": # Ha az üzenet a pokemon.com-tól jött
            link = message["body"]["html"].split("href=")[1].split(">")[0].strip('"') # Kinyerjük az aktiváló linket az html kódból
            return link

def open_activation_link(link, proxies):
    # Ez a függvény megnyitja az aktiváló linket és visszaigazolja a fiókot
    response = requests.get(link, proxies=proxies) # Megnyitjuk a linket
    return response

def save_account_to_file(username, password):
    # Ez a függvény elmenti a sikeresen regisztrált és aktivált fiókot egy fájlba
    with open(file_name, "a") as file: # Megnyitjuk a fájlt írási módban
        file.write(f"{username},{password}\n") # Hozzáírjuk a fiók adatait a következő sorba

def main():
    # Ez a fő függvény, ami meghívja az előző függvényeket egy ciklusban annyiszor, ahány fiókot szeretnénk létrehozni
    n = 10 # A fiókok száma
    start_time = time.time() # Elmentjük az indulási időt
    proxy_counter = collections.Counter() # Létrehozunk egy számlálót a proxyk használatára
    for i in tqdm.tqdm(range(n)): # Létrehozunk egy folyamatjelzőt a ciklusra
        print(f"Creating account {i+1} of {n}...")
        username, password = generate_username_password() # Generálunk felhasználónevet és jelszót
        email, address = get_temp_email() # Kérünk ideiglenes email címet
        proxy = get_proxy() # Választunk proxyt
        while not check_proxy(proxy): # Amíg a proxy nem jó
            print(f"Bad proxy: {proxy}")
            proxy = get_proxy() # Választunk másik proxyt
        print(f"Good proxy: {proxy}")
        proxy_counter.update([proxy]) # Növeljük a számlálót a proxyval
        if proxy_counter[proxy] > proxy_limit: # Ha elérte a limitet a proxy
            print(f"Proxy limit reached: {proxy}")
            break # Kilépünk a ciklusból
        registration_response = send_registration_request(username, password, address, proxy) # Elküldjük a regisztrációs kérést
        if registration_response.status_code == 200: # Ha a kérés sikeres volt
            print(f"Registration successful for {username}")
            activation_link = check_email_account(email) # Ellenőrizzük az email fiókot
            if activation_link: # Ha találtunk aktiváló linket
                activation_response = open_activation_link(activation_link, proxy) # Megnyitjuk az aktiváló linket
                if activation_response.status_code == 200: # Ha a kérés sikeres volt
                    print(f"Activation successful for {username}")
                    accounts.append((username, password, address)) # Hozzáadjuk a fiókot a listához
                    save_account_to_file(username, password) # Elmentjük a fiókot a fájlba
                else: # Ha a kérés sikertelen volt
                    print(f"Activation failed for {username}")
            else: # Ha nem találtunk aktiváló linket
                print(f"No activation link found for {username}")
        else: # Ha a kérés sikertelen volt
            print(f"Registration failed for {username}")
    end_time = time.time() # Elmentjük a befejezési időt
    elapsed_time = end_time - start_time # Kiszámoljuk az eltelt időt
    print(f"Done. Created {len(accounts)} accounts in {elapsed_time:.2f} seconds.")
    print(accounts) # Kiírjuk a létrehozott fiókokat

# Futtatjuk a fő függvényt
if __name__ == "__main__":
    main()
