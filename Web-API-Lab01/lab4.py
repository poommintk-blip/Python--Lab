import requests

def get_country_info(country_name):
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # restcountries API returns a list of results
        country = data[0]
        
        # Extract required fields
        name = country.get('name', {}).get('common', 'N/A')
        capital_list = country.get('capital', ['N/A'])
        capital = capital_list[0] if capital_list else 'N/A'
        region = country.get('region', 'N/A')
        population = country.get('population', 'N/A')
        
        # languages are in a dictionary: { code: name }
        langs = country.get('languages', {})
        languages = ", ".join(langs.values()) if langs else 'N/A'
        
        print("=== Country Info ===")
        print(f"Name: {name}")
        print(f"Capital: {capital}")
        print(f"Region: {region}")
        print(f"Population: {population}")
        print(f"Languages: {languages}")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # Expected: Error: country not found
            print("Error: country not found")
        else:
            print(f"Error: HTTP {e.response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    country = input("Enter country: ").strip()
    get_country_info(country)
