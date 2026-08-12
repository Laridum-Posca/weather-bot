

import io
import time
import requests

# --- Credentials ---
TELEGRAM_BOT_TOKEN = "8640033038:AAGldat7FLj8GP34NwQWGPPF9jLBJ8TRB0o"
TELEGRAM_CHAT_ID = "6116503072"
API_KEY = "393397b99f19e1ae5f46a347ac48b87b"

# Target locations mapped to precise coordinates
TARGET_LOCATIONS = {
    "Balanga City": {"lat": 14.6788, "lon": 120.5402},
    "Dinalupihan": {"lat": 14.8728, "lon": 120.4594},
    "Manila": {"lat": 14.5995, "lon": 120.9842},
    "San Fernando": {"lat": 15.0284, "lon": 120.6893},
}

# SSEC (University of Wisconsin-Madison) West Pacific sector snapshot
SATELLITE_IMAGE_URL = (
    "https://www.ssec.wisc.edu/data/geo/images/himawari09/latest-himawari09_rgb_wp.jpg"
)


def send_telegram_alert(message):
  """Sends the text-based weather report via Telegram."""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload, timeout=20)
    if response.status_code == 200:
      print("📲 Automated weather text sent successfully!")
    else:
      print(f"❌ Failed to send text: {response.text}")
  except Exception as e:
    print(f"❌ Text transmission error: {e}")


def send_telegram_photo_safely(photo_url, caption):
  """Downloads the image locally with headers to avoid blocks, then uploads to Telegram."""
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

  headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
  }

  try:
    print("🛰️ Downloading satellite image securely...")
    img_response = requests.get(photo_url, headers=headers, timeout=20)
    img_response.raise_for_status()

    photo_file = io.BytesIO(img_response.content)
    photo_file.name = "philippines_satellite.jpg"

    payload = {"chat_id": TELEGRAM_CHAT_ID, "caption": caption, "parse_mode": "Markdown"}
    files = {"photo": photo_file}

    response = requests.post(url, data=payload, files=files, timeout=30)
    if response.status_code == 200:
      print("🛰️ Satellite image uploaded and sent successfully!")
    else:
      print(f"❌ Failed to upload photo to Telegram: {response.text}")
  except Exception as e:
    print(f"❌ Photo transmission error: {e}")


def job_fetch_and_send():
  """Fetches weather data using coordinates and pushes updates to Telegram."""
  print("\n[Executing automated task] Fetching weather updates via coordinates...")

  master_message = "🌤 **Multi-City Daily Weather Brief**\n================================\n"

  for city_name, coords in TARGET_LOCATIONS.items():
    lat = coords["lat"]
    lon = coords["lon"]
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    )

    try:
      response = requests.get(url, timeout=20)
      response.raise_for_status()
      data = response.json()

      temp = data["main"]["temp"]
      feels_like = data["main"]["feels_like"]
      description = data["weather"][0]["description"]
      humidity = data["main"]["humidity"]
      wind_speed = data["wind"]["speed"]
      location_name = data.get("name", city_name)

      desc_lower = description.lower()
      if "heavy intensity rain" in desc_lower or "thunderstorm" in desc_lower:
        alert = "🔴 RED WARNING (Flooding possible! Stay indoors if you can.)"
      elif "moderate rain" in desc_lower or "rain" in desc_lower:
        alert = "🟠 ORANGE WARNING (Bring an umbrella/raincoat, roads might get wet.)"
      elif "light rain" in desc_lower or "drizzle" in desc_lower:
        alert = "🟡 YELLOW ADVISORY (Light showers expected, maybe pack a light shield.)"
      else:
        alert = "🟢 ALL CLEAR (No major rain expected, you're good to go!)"

      master_message += (
          f"\n📍 **{location_name}**\n"
          f"🌡 Temp: {temp}°C (Feels like {feels_like}°C)\n"
          f"☁️ Conditions: {description.capitalize()}\n"
          f"💧 Humidity: {humidity}% | 💨 Wind: {wind_speed} m/s\n"
          f"📢 Advisory: {alert}\n"
          f"--------------------------------"
      )

    except Exception as err:
      print(f"❌ Error fetching data for {city_name}: {err}")
      master_message += f"\n📍 **{city_name}**: ❌ Failed to fetch data.\n--------------------------------"

  # 1. Send the combined multi-city text breakdown
  send_telegram_alert(master_message)

  # 2. Download and push satellite map image
  image_caption = (
      "🛰️ **Latest Himawari-9 True Color Satellite Snapshot (West Pacific / Philippines)**\n"
      "Source: SSEC, University of Wisconsin-Madison"
  )
  send_telegram_photo_safely(SATELLITE_IMAGE_URL, image_caption)


if __name__ == "__main__":
  print("🤖 Multi-City Coordinate Weather Bot initialized. Running...")

  job_fetch_and_send()

  while True:
    time.sleep(86400)
    job_fetch_and_send()