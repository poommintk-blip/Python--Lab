from fastapi import FastAPI, HTTPException
import requests
from typing import List, Optional

app = FastAPI(title="Network Programming Lab 01 API")

# --- Task 1: GitHub User Info ---
@app.get("/github/{username}")
def get_github_user(username: str):
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="GitHub API Error")
    
    data = response.json()
    return {
        "name": data.get("name"),
        "public_repos": data.get("public_repos"),
        "followers": data.get("followers"),
        "following": data.get("following")
    }

# --- Task 2: Top Python Repos ---
@app.get("/search/python")
def get_top_python_repos(limit: int = 3):
    url = "https://api.github.com/search/repositories"
    params = {
        'q': 'language:python',
        'sort': 'stars',
        'order': 'desc',
        'per_page': limit
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="GitHub API Error")
    
    data = response.json()
    repos = []
    for item in data.get('items', []):
        repos.append({
            "name": item.get('name'),
            "stars": item.get('stargazers_count'),
            "url": item.get('html_url')
        })
    return {"top_python_repos": repos}

# --- Task 4: Country Info ---
@app.get("/country/{country_name}")
def get_country(country_name: str):
    url = f"https://restcountries.com/v3.1/name/{country_name}"
    response = requests.get(url)
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Country not found")
    elif response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="RestCountries API Error")
    
    data = response.json()
    country = data[0]
    
    langs = country.get('languages', {})
    languages = list(langs.values())
    
    return {
        "name": country.get('name', {}).get('common'),
        "capital": country.get('capital', ["N/A"])[0],
        "region": country.get('region'),
        "population": country.get('population'),
        "languages": languages
    }

@app.get("/")
def root():
    return {
        "message": "Welcome to Lab 01 Network Programming FastAPI",
        "endpoints": {
            "github_user": "/github/{username}",
            "top_python_repos": "/search/python",
            "country_info": "/country/{country_name}"
        },
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
