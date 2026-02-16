from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

app = Flask(__name__)
CORS(app)

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
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return response.json()['link']
        else:
            print(f"Bitly error: {response.status_code}")
            return long_url
    except Exception as e:
        print(f"Bitly exception: {e}")
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
        decoded_url = urllib.parse.unquote(url)
        
        # Extrakce názvu hotelu
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
            'zanzibar': '🇹🇿', 'mexiko': '🇲🇽', 'dominikana': '🇩🇴', 'kuba': '🇨🇺',
            'mauricius': '🇲🇺', 'indonesie': '🇮🇩', 'bali': '🇮🇩'
        }
        
        dest_lower = info['destination'].lower()
        info['flag'] = country_flags.get(dest_lower, '🌍')
        
    except Exception as e:
        print(f"Error extracting from URL: {e}")
    
    return info

def scrape_cedok_page(url):
    """Stáhne a parsuje Čedok stránku"""
    info = extract_info_from_url(url)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return info
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Hledání ceny
        price_patterns = [
            {'class': re.compile(r'price', re.I)},
            {'class': re.compile(r'amount', re.I)},
        ]
        
        for pattern in price_patterns:
            price_elem = soup.find(['span', 'div', 'p'], pattern)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'(\d[\d\s]*)', price_text)
                if price_match:
                    price_num = price_match.group(1).replace(' ', '')
                    info['price'] = f"{price_num} Kč"
                    break
        
        # Hledání hvězdiček s role="listitem"
        stars_found = False
        star_icons = soup.find_all('i', {'class': re.compile(r'icon.*star', re.I), 'role': 'listitem'})
        if star_icons and len(star_icons) <= 5:
            info['stars'] = len(star_icons)
            stars_found = True
        
        if not stars_found:
            rating_list = soup.find('span', {'role': 'list'})
            if rating_list:
                star_icons = rating_list.find_all('i', class_=re.compile(r'icon.*star', re.I))
                if star_icons and len(star_icons) <= 5:
                    info['stars'] = len(star_icons)
        
        # Získání textu stránky
        page_text_lower = soup.get_text().lower()
        
        # Hledání termínu
        date_patterns = [
            r'(\d{1,2}\.\d{1,2}\s*-\s*\d{1,2}\.\d{1,2}\.\d{4})',
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, page_text_lower)
            if date_match:
                info['date'] = date_match.group(1).strip()
                break
        
        # Hledání počtu dní
        days_patterns = [
            r'\((\d+)\s+dn[yíů],?\s+\d+\s+noc[íi]\)',
            r'(\d+)\s+dn[yíů],?\s+\d+\s+noc[íi]',
            r'(\d+)\s+dn[yíů]\b',
            r'(\d+)\s+dnů\b',
            r'(\d+)\s+dní\b',
        ]
        
        found_days = False
        for pattern in days_patterns:
            days_match = re.search(pattern, page_text_lower)
            if days_match:
                info['days'] = int(days_match.group(1))
                found_days = True
                break
        
        # Výpočet z termínu pokud nenalezeno
        if not found_days and info['date']:
            try:
                date_parts = info['date'].replace(' ', '').split('-')
                if len(date_parts) == 2:
                    start_day = int(date_parts[0].split('.')[0])
                    end_parts = date_parts[1].split('.')
                    end_day = int(end_parts[0])
                    info['days'] = end_day - start_day + 1
            except:
                pass
        
        # Hledání stravy
        meal_keywords = {
            'all inclusive': 'All Inclusive',
            'ultra all inclusive': 'Ultra All Inclusive',
            'polopenze': 'Polopenze',
            'plná penze': 'Plná penze',
            'snídaně': 'Snídaně',
            'snidane': 'Snídaně',
            'bez stravy': 'Bez stravy',
        }
        
        for keyword, meal_type in meal_keywords.items():
            if keyword in page_text_lower:
                info['meals'] = meal_type
                break
        
    except Exception as e:
        print(f"Scraping error: {e}")
    
    return info

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL je povinná'}), 400
        
        # Scraping dat
        info = scrape_cedok_page(url)
        
        # Vytvoření affiliate URL
        affiliate_url = f"{AFFILIATE_PREFIX}?url={urllib.parse.quote(url)}"
        
        # Zkrácení přes Bitly
        short_url = shorten_with_bitly(affiliate_url)
        
        # Generování šablon
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
        
        return jsonify({
            'success': True,
            'channel_template': channel_template,
            'web_template': web_template,
            'short_url': short_url,
            'info': info
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
