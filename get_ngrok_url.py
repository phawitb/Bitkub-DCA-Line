import requests

def get_ngrok_url():
    try:
        response = requests.get("http://127.0.0.1:4040/api/tunnels")
        data = response.json()

        tunnels = data.get("tunnels", [])
        for tunnel in tunnels:
            if tunnel["proto"] == "https":
                return tunnel["public_url"]
        return tunnels[0]["public_url"] if tunnels else None

    except Exception as e:
        print("❌ Error fetching Ngrok URL:", e)
        return None

def save_to_config_file(url, filename="frontend/config.txt"):
    try:
        with open(filename, "w") as f:
            f.write(f"NGROK_URL={url}\n")
        print(f"✅ Ngrok URL saved to {filename}")
    except Exception as e:
        print("❌ Error saving to file:", e)

if __name__ == "__main__":
    ngrok_url = get_ngrok_url()
    if ngrok_url:
        print("Ngrok URL:", ngrok_url)
        save_to_config_file(ngrok_url)
    else:
        print("No Ngrok URL found.")
