import requests

def search_top_python_repos():
    url = "https://api.github.com/search/repositories"
    params = {
        'q': 'language:python',
        'sort': 'stars',
        'order': 'desc',
        'per_page': 3
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        print("=== Top Python Repos ===")
        for index, repo in enumerate(data.get('items', []), start=1):
            name = repo.get('name')
            stars = repo.get('stargazers_count')
            url = repo.get('html_url')
            print(f"{index}. {name}")
            print(f"   stars: {stars}")
            print(f"   url: {url}")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    search_top_python_repos()
