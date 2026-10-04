import requests
import json
import time


# =========================
# Configuration
# =========================

BOT_TOKEN = "8655248376:AAF7RGjJdUjNWAhppKKIqPIb0R2oNf0YE3o"
EXTERNAL_API_URL = "35741544"

TELEGRAM_API = "https://api.telegram.org/bot" + BOT_TOKEN


# =========================
# Send Telegram message
# =========================

def send_message(chat_id, text, keyboard=None):
    url = TELEGRAM_API + "/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if keyboard is not None:
        data["reply_markup"] = json.dumps(keyboard)

    try:
        response = requests.post(
            url,
            data=data,
            timeout=30
        )

        response.raise_for_status()
        return response.json()

    except Exception as error:
        print("sendMessage error:", error)
        return None


# =========================
# Main keyboard
# =========================

def main_keyboard():
    return {
        "keyboard": [
            [
                {
                    "text": "📱 Phone Lookup"
                }
            ]
        ],
        "resize_keyboard": True
    }


# =========================
# Welcome
# =========================

def welcome(chat_id):
    text = (
        "👋 Welcome!\n\n"
        "Please select an option below."
    )

    send_message(
        chat_id,
        text,
        main_keyboard()
    )


# =========================
# Phone validation
# =========================

def valid_phone(phone):
    return len(phone) == 10 and phone.isdigit()


# =========================
# External API
# =========================

def call_external_api(phone):
    if EXTERNAL_API_URL == "":
        return {
            "error": "EXTERNAL_API_URL is not configured."
        }

    try:
        response = requests.get(
            EXTERNAL_API_URL,
            params={
                "phone": phone
            },
            timeout=30
        )

        response.raise_for_status()

        # Convert API response to JSON
        return response.json()

    except requests.exceptions.RequestException as error:
        return {
            "error": "External API request failed.",
            "details": str(error)
        }

    except ValueError:
        return {
            "error": "External API did not return valid JSON."
        }


# =========================
# Process message
# =========================

def handle_message(message):
    if "chat" not in message:
        return

    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    if text == "":
        return

    # /start
    if text == "/start":
        welcome(chat_id)
        return

    # Phone lookup button
    if text == "📱 Phone Lookup":
        send_message(
            chat_id,
            "📞 Send 10 digit mobile number:"
        )
        return

    # Numeric input
    if text.isdigit():

        if not valid_phone(text):
            send_message(
                chat_id,
                "❌ Invalid mobile number.\n\n"
                "Please send exactly 10 digits."
            )
            return

        send_message(
            chat_id,
            "🔎 Processing..."
        )

        result = call_external_api(text)

        formatted = json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )

        send_message(
            chat_id,
            "<pre>" + formatted + "</pre>"
        )

        return

    # Invalid input
    send_message(
        chat_id,
        "❌ Invalid input.\n\n"
        "Please press 📱 Phone Lookup and "
        "send a 10 digit mobile number."
    )


# =========================
# Long polling
# =========================

def main():

    if BOT_TOKEN == "":
        print("ERROR: BOT_TOKEN is empty.")
        print("Add your Telegram bot token first.")
        return

    offset = None

    print("Bot started.")
    print("Waiting for messages...")

    while True:

        try:
            params = {
                "timeout": 30
            }

            if offset is not None:
                params["offset"] = offset

            response = requests.get(
                TELEGRAM_API + "/getUpdates",
                params=params,
                timeout=35
            )

            response.raise_for_status()

            data = response.json()

            if not data.get("ok"):
                print("Telegram API error:", data)
                time.sleep(3)
                continue

            updates = data.get("result", [])

            for update in updates:

                # Advance offset
                offset = update["update_id"] + 1

                if "message" in update:
                    handle_message(update["message"])

        except requests.exceptions.RequestException as error:
            print("Network error:", error)
            time.sleep(5)

        except ValueError:
            print("Invalid JSON response.")
            time.sleep(3)

        except Exception as error:
            print("Unexpected error:", error)
            time.sleep(3)


# =========================
# Start bot
# =========================

if __name__ == "__main__":
    main()
