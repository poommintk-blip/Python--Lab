import requests

def main():
    city = input("Enter city: ")

    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city,
        "count": 3,
        "language": "en"
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        if "results" not in data:
            print("Error: city not found")
            return

        print(f"=== Search Results: {city} ===")
        for i, result in enumerate(data["results"], 1):
            name = result.get("name", "N/A")
            country = result.get("country", "N/A")
            lat = result.get("latitude", "N/A")
            lon = result.get("longitude", "N/A")
            print(f"{i}. {name}, {country}")
            print(f"   Lat: {lat}, Lon: {lon}")

    except requests.exceptions.Timeout:
        print("Error: Request timed out")
    except requests.exceptions.HTTPError as e:
        print(f"Error: HTTP error occurred - {e}")
    except requests.exceptions.RequestException as e:
        print(f"Error: Request failed - {e}")


if __name__ == "__main__":
    main()