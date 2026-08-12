from datetime import datetime
from zoneinfo import ZoneInfo
import time
import requests
from requests.adapters import HTTPAdapter, Retry

# Configured Credentials & Target Cities
TELEGRAM_BOT_TOKEN = "8640033038:AAGldat7FLj8GP34NwQWGPPF9jLBJ8TRB0o"
TELEGRAM_CHAT_ID = "6116503072"
WEATHER_API_KEY = "393397b99f19e1ae5f46a347ac48b87b"
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Multi-city configuration
CITIES = ["Balanga", "Dinalupihan", "San Fernando", "Manila"]

def create_robust_session():
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def get_color_signal(temp, description):
    """Determine color signal based on weather condition and temperature."""
    desc_lower = description.lower()
    if "rain" in desc_lower or "storm" in desc_lower or "thunder" in desc_lower:
        return "🔴 Red Signal (Heavy Weather / Rain Alert)"
    elif temp > 33 or "clear" in desc_lower:
        return "🟡 Yellow Signal (High Heat / Sunny Conditions)"
    else:
        return "🟢 Green Signal (Stable / Normal Conditions)"

def send_weather_updates():
    session = create_robust_session()
    ph_timezone = ZoneInfo("Asia/Manila")
    
    for city in CITIES:
        params = {
            "q": city,
            "appid": WEATHER_API_KEY,
            "units": "metric"
        }
        
        try:
            response = session.get(WEATHER_API_URL, params=params, timeout=10)
            
            if response.status_code == 429:
                print(f"Rate limit hit while fetching {city}. Waiting before retry...")
                time.sleep(5)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            # Handle timezone and lock strictly to Philippine Standard Time (PST)
            utc_timestamp = data.get("dt")
            if utc_timestamp:
                local_time = datetime.fromtimestamp(utc_timestamp, tz=ZoneInfo("UTC")).astimezone(ph_timezone)
                formatted_time = local_time.strftime("%B %d, %Y - %I:%M %p")
            else:
                formatted_time = datetime.now(ph_timezone).strftime("%B %d, %Y - %I:%M %p")
                
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"].capitalize()
            humidity = data["main"]["humidity"]
            icon_code = data["weather"][0]["icon"]
            
            # Color signal evaluation
            color_signal = get_color_signal(temp, desc)
            
            message = (
                f"🌤️ **Automated Weather Report**\n"
                f"📍 Location: {city}\n"
                f"🕒 Time: {formatted_time} (PST)\n"
                f"🌡️ Temp: {temp}°C\n"
                f"☁️ Condition: {desc}\n"
                f"💧 Humidity: {humidity}%\n"
                f"🎨 Status: {color_signal}\n\n"
                f"📝 **Notes:** Routine monitoring active for regional coverage."
            )
            
            # Weather icon graphic / satellite map representation URL
            photo_url = f"https://openweathermap.org/img/wn/{icon_code}@4x.png"
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
            payload = {
                "chat_id": TELEGRAM_CHAT_ID,
                "photo": photo_url,
                "caption": message,
                "parse_mode": "Markdown"
            }
            
            tg_response = session.post(url, json=payload, timeout=10)
            if tg_response.status_code == 200:
                print(f"Weather update for {city} sent successfully!")
            else:
                print(f"Failed to send update for {city}: {tg_response.text}")
                
            # Brief pause between city requests to respect API rate boundaries
            time.sleep(2)
            
        except requests.exceptions.RequestException as e:
            print(f"Weather API request failed for {city}: {e}")
        except KeyError as e:
            print(f"Unexpected JSON structure for {city}, missing key: {e}")

if __name__ == "__main__":
    send_weather_updates()
