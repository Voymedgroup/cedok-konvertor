#!/usr/bin/env python3
"""
Čedok URL Konvertor
Automaticky extrahuje data z Čedok URL, vytvoří affiliate link, zkrátí přes Bitly
a vygeneruje šablony pro kanál i web.
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse
import sys
import re

# Konfigurace
BITLY_TOKEN = '50e591e73398864b51928b3443ab03d817af94d0'
AFFILIATE_PREFIX = 'https://www.jdoqocy.com/click-100430731-15693379'

def shorten_with_bitly(long_url):
    """Zkrátí URL přes Bitly API"""
    try:
        response = requests.post(
            'https://api-ssl.bitly.com/v4/shorten',
            headers={
                'Authorization': f'Bearer {BITLY_TOKEN}',
                'Content-Type': 'application/json',
            },
            json={
                'long_url': long_url,
                'domain': 'bit.ly'
            }
        )
        
        if response.status_code in [200, 201]:
            return response.json()['link']
        else:
            print(f"⚠️  Bitly chyba: {response.status_code}")
            return long_url
    except Exception as e:
        print(f"⚠️  Chyba při zkracování: {e}")
        return long_url

def extract_info_from_url(url):
    """Extrahuje základní info z URL struktury"""
    info = {
        'hotel_name': '',
        'destination': '',
        'flag': '🌍',
        'days': 8,
        'date': '',
        'stars': 4,
        'meals': 'All Inclusive',
        'price': '0 Kč'
    }
    
    try:
        # Dekódování URL
        decoded_url = urllib.parse.unquote(url)
        
        # Extrakce názvu hotelu z path
        hotel_match = re.search(r'/hotel-([^,]+)', decoded_url)
        if hotel_match:
            hotel_parts = hotel_match.group(1).replace('(', '').replace(')', '').split('-')
            info['hotel_name'] = ' '.join(word.capitalize() for word in hotel_parts)
        
        # Detekce hvězdiček podle značky hotelu
        hotel_name_lower = info['hotel_name'].lower()
        luxury_brands = ['hilton', 'marriott', 'hyatt', 'intercontinental', 'shangri-la', 'four seasons', 'ritz-carlton', 'waldorf', 'st. regis', 'aryaduta', 'grand hyatt', 'jw marriott', 'park hyatt', 'sofitel', 'kempinski', 'mandarin oriental', 'peninsula', 'raffles', 'oberoi', 'taj']
        upper_brands = ['doubletree', 'courtyard', 'sheraton', 'westin', 'radisson', 'novotel', 'pullman', 'renaissance', 'crowne plaza', 'mercure']
        mid_brands = ['holiday inn', 'ibis', 'best western', 'ramada', 'comfort inn', 'quality inn']
        
        if any(brand in hotel_name_lower for brand in luxury_brands):
            info['stars'] = 5
        elif any(brand in hotel_name_lower for brand in upper_brands):
            info['stars'] = 4
        elif any(brand in hotel_name_lower for brand in mid_brands):
            info['stars'] = 3
        
        # Extrakce destinace
        dest_match = re.search(r'/dovolena/([^/]+)/', decoded_url)
        if dest_match:
            info['destination'] = dest_match.group(1).capitalize()
        
        # Mapa vlajek
        country_flags = {
            'egypt': '🇪🇬', 'recko': '🇬🇷', 'grecko': '🇬🇷', 'spanelsko': '🇪🇸',
            'turecko': '🇹🇷', 'chorvatsko': '🇭🇷', 'italie': '🇮🇹', 'bulharsko': '🇧🇬',
            'kypr': '🇨🇾', 'tunisko': '🇹🇳', 'maroko': '🇲🇦', 'oman': '🇴🇲',
            'dubaj': '🇦🇪', 'uae': '🇦🇪', 'thajsko': '🇹🇭', 'maledivy': '🇲🇻',
            'zanzibar': '🇹🇿', 'mexiko': '🇲🇽', 'dominikana': '🇩🇴', 'kuba': '🇨🇺'
        }
        
        dest_lower = info['destination'].lower()
        info['flag'] = country_flags.get(dest_lower, '🌍')
        
    except Exception as e:
        print(f"⚠️  Chyba při extrakci z URL: {e}")
    
    return info

def scrape_cedok_page(url):
    """Stáhne a parsuje Čedok stránku pro získání přesných dat"""
    info = extract_info_from_url(url)
    
    try:
        print("📥 Stahuji data z Čedok...")
        
        # Přidáme User-Agent aby nás web nepovažoval za bota
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️  Nepodařilo se stáhnout stránku (status: {response.status_code})")
            print("ℹ️  Použiji základní data z URL...")
            return info
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hledání ceny
        price_patterns = [
            {'class': re.compile(r'price', re.I)},
            {'class': re.compile(r'amount', re.I)},
            {'itemprop': 'price'},
            {'data-price': True}
        ]
        
        for pattern in price_patterns:
            price_elem = soup.find(['span', 'div', 'p'], pattern)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extrakce čísel z textu
                price_match = re.search(r'(\d[\d\s]*)', price_text)
                if price_match:
                    price_num = price_match.group(1).replace(' ', '')
                    info['price'] = f"{price_num} Kč"
                    print(f"✅ Cena nalezena: {info['price']}")
                    break
        
        # Hledání hvězdiček - vylepšené
        # Hledáme přímo ikony s role="listitem" (Čedok používá tento atribut pro hodnocení)
        stars_found = False
        
        # Najdeme všechny hvězdičky s role="listitem"
        star_icons = soup.find_all('i', {'class': re.compile(r'icon.*star', re.I), 'role': 'listitem'})
        if star_icons and len(star_icons) <= 5:
            info['stars'] = len(star_icons)
            print(f"✅ Hodnocení (z ikon s role=listitem): {info['stars']}⭐")
            stars_found = True
        
        # Fallback - pokud nenajdeme s role=listitem, zkusíme najít v parent containeru
        if not stars_found:
            # Hledáme span s role="list" který obsahuje rating stars
            rating_list = soup.find('span', {'role': 'list'})
            if rating_list:
                star_icons = rating_list.find_all('i', class_=re.compile(r'icon.*star', re.I))
                if star_icons and len(star_icons) <= 5:
                    info['stars'] = len(star_icons)
                    print(f"✅ Hodnocení (z role=list): {info['stars']}⭐")
                    stars_found = True
        
        # Fallback - hledání v textu
        if not stars_found:
            star_patterns = [
                {'class': re.compile(r'star', re.I)},
                {'class': re.compile(r'rating', re.I)}
            ]
            
            for pattern in star_patterns:
                stars_elem = soup.find(['span', 'div'], pattern)
                if stars_elem:
                    stars_text = stars_elem.get_text(strip=True)
                    stars_match = re.search(r'(\d)', stars_text)
                    if stars_match:
                        stars_num = int(stars_match.group(1))
                        if stars_num <= 5:  # Sanity check
                            info['stars'] = stars_num
                            print(f"✅ Hodnocení (z textu): {info['stars']}⭐")
                            break
        
        # Získání textu stránky pro další zpracování
        page_text_lower = soup.get_text().lower()
        
        # Hledání termínu (datum)
        date_patterns = [
            r'(\d{1,2}\.\d{1,2}\s*-\s*\d{1,2}\.\d{1,2}\.\d{4})',  # 12.05 - 15.05.2026
            r'termín[:\s]*(\d{1,2}\.\d{1,2}\s*-\s*\d{1,2}\.\d{1,2}\.\d{4})',
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, page_text_lower)
            if date_match:
                info['date'] = date_match.group(1).strip()
                print(f"✅ Termín: {info['date']}")
                break
        
        # Hledání počtu dní - hledáme konkrétně vzor "X dny, Y noci" nebo "X dní"
        days_patterns = [
            r'\((\d+)\s+dn[yíů],?\s+\d+\s+noc[íi]\)',  # (7 dní, 5 nocí)
            r'(\d+)\s+dn[yíů],?\s+\d+\s+noc[íi]',  # 7 dní, 5 nocí
            r'(\d+)\s+dn[yíů]\b',  # 7 dny
            r'(\d+)\s+dnů\b',  # 7 dnů
            r'(\d+)\s+dní\b',  # 7 dní
        ]
        
        found_days = False
        for pattern in days_patterns:
            days_match = re.search(pattern, page_text_lower)
            if days_match:
                info['days'] = int(days_match.group(1))
                print(f"✅ Počet dní: {info['days']}")
                found_days = True
                break
        
        # Pokud jsme nenašli dny v textu, zkusíme spočítat z termínu
        if not found_days and info['date']:
            try:
                # Parsujeme datum ve formátu 09.09 - 15.09.2026
                date_parts = info['date'].replace(' ', '').split('-')
                if len(date_parts) == 2:
                    start_day = int(date_parts[0].split('.')[0])
                    end_parts = date_parts[1].split('.')
                    end_day = int(end_parts[0])
                    # Výpočet: konec - začátek + 1
                    info['days'] = end_day - start_day + 1
                    print(f"✅ Počet dní (vypočítáno z termínu): {info['days']}")
                    found_days = True
            except Exception as calc_error:
                print(f"⚠️  Chyba při výpočtu dní z termínu: {calc_error}")
        
        # Hledání stravy - vylepšené klíčová slova
        meal_keywords = {
            'all inclusive': 'All Inclusive',
            'ultra all inclusive': 'Ultra All Inclusive',
            'polopenze': 'Polopenze',
            'plná penze': 'Plná penze', 
            'plna penze': 'Plná penze',
            'snídaně': 'Snídaně',
            'snidane': 'Snídaně',
            'bez stravy': 'Bez stravy',
            'pouze ubytování': 'Bez stravy',
            'light all inclusive': 'Light All Inclusive',
        }
        
        for keyword, meal_type in meal_keywords.items():
            if keyword in page_text_lower:
                info['meals'] = meal_type
                print(f"✅ Strava: {info['meals']}")
                break
        
        # Upřesnění názvu hotelu ze stránky
        title_tag = soup.find('h1')
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            if 'hotel' in title_text.lower():
                info['hotel_name'] = title_text
                print(f"✅ Hotel: {info['hotel_name']}")
        
    except requests.Timeout:
        print("⚠️  Timeout - stránka se načítá příliš dlouho")
        print("ℹ️  Použiji základní data z URL...")
    except Exception as e:
        print(f"⚠️  Chyba při scrapingu: {e}")
        print("ℹ️  Použiji základní data z URL...")
    
    return info

def generate_templates(info, short_url, affiliate_url):
    """Vygeneruje šablony pro kanál a web"""
    
    # Pokud máme termín, přidáme ho do šablony
    date_text = f" ({info['date']})" if info['date'] else ""
    
    channel_template = f"""Odkaz: {short_url}
🌞 Last Minute Zájezd
{info['flag']} {info['hotel_name']}, {info['destination']}
📅 Na {info['days']} dní{date_text}
✈️ Letenky a 🏨 ubytování ve {info['stars']}⭐️ hotelu
🍽️ Strava: {info['meals']}
💰 {info['price']}"""

    web_template = f"""{info['hotel_name']}
{info['flag']} {info['destination']}
📅 Na {info['days']} dní{date_text}
✈️ Letenky a 🏨 ubytování ve {info['stars']}⭐️ hotelu
🍽️ Strava: {info['meals']}
💰 {info['price']}
{affiliate_url}"""

    return channel_template, web_template

def main():
    print("=" * 60)
    print("🚀 ČEDOK URL KONVERTOR")
    print("=" * 60)
    print()
    
    # Získání URL od uživatele
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Vložte Čedok URL: ").strip()
    
    if not url:
        print("❌ Nebyla zadána žádná URL!")
        sys.exit(1)
    
    print()
    print("⚙️  Zpracovávám...")
    print()
    
    # 1. Scraping dat
    info = scrape_cedok_page(url)
    
    # 2. Vytvoření affiliate URL
    affiliate_url = f"{AFFILIATE_PREFIX}?url={urllib.parse.quote(url)}"
    print(f"✅ Affiliate URL vytvořena")
    
    # 3. Zkrácení přes Bitly
    print("🔗 Zkracuji URL přes Bitly...")
    short_url = shorten_with_bitly(affiliate_url)
    print(f"✅ Zkrácená URL: {short_url}")
    
    # 4. Generování šablon
    channel_template, web_template = generate_templates(info, short_url, affiliate_url)
    
    print()
    print("=" * 60)
    print("📱 ŠABLONA NA KANÁL")
    print("=" * 60)
    print()
    print(channel_template)
    print()
    print("=" * 60)
    print("🌐 ŠABLONA NA WEB")
    print("=" * 60)
    print()
    print(web_template)
    print()
    print("=" * 60)
    print("✅ HOTOVO!")
    print("=" * 60)

if __name__ == "__main__":
    main()
