from datetime import datetime
from zoneinfo import ZoneInfo
import time
import requests
from requests.adapters import HTTPAdapter, Retry

# Configured Credentials
TELEGRAM_BOT_TOKEN = "8640033038:AAGldat7FLj8GP34NwQWGPPF9jLBJ8TRB0o"
TELEGRAM_CHAT_ID = "6116503072"
WEATHER_API_KEY = "393397b99f19e1ae5f46a347ac48b87b"
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"
CITY = "Balanga"

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

def send_weather_update():
    session = create_robust_session()
    
    params = {
        "q": CITY,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }
    
    try:
        response = session.get(WEATHER_API_URL, params=params, timeout=10)
        
        if response.status_code == 429:
            print("Rate limit hit. Waiting before retry...")
            time.sleep(5)
            return
            
        response.raise_for_status()
        data = response.json()
        
        # Handle timezone and lock strictly to Philippine Standard Time (PST)
        ph_timezone = ZoneInfo("Asia/Manila")
        utc_timestamp = data.get("dt")
        
        if utc_timestamp:
            local_time = datetime.fromtimestamp(utc_timestamp, tz=ZoneInfo("UTC")).astimezone(ph_timezone)
            formatted_time = local_time.strftime("%B %d, %Y - %I:%M %p")
        else:
            formatted_time = datetime.now(ph_timezone).strftime("%B %d, %Y - %I:%M %p")
            
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]
        
        message = (
            f"🌤️ **Automated Weather Report**\n"
            f"📍 Location: {CITY}\n"
            f"🕒 Time: {formatted_time} (PST)\n"
            f"🌡️ Temp: {temp}°C\n"
            f"☁️ Condition: {desc}\n"
            f"💧 Humidity: {humidity}%"
        )
        
    except requests.exceptions.RequestException as e:
        print(f"Weather API request failed: {e}")
        return
    except KeyError as e:
        print(f"Unexpected JSON data structure from weather API, missing key: {e}")
        return

    # Send the structured message via Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        tg_response = session.post(url, json=payload, timeout=10)
        if tg_response.status_code == 200:
            print("Weather update sent successfully!")
        else:
            print(f"Failed to send message: {tg_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Telegram API request failed: {e}")

if __name__ == "__main__":
    send_weather_update()
