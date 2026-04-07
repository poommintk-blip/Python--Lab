import requests

def get_github_user(username):
    url = f"https://api.github.com/users/{username}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("=== GitHub User Info ===")
        print(f"Name: {data.get('name')}")
        print(f"Public repos: {data.get('public_repos')}")
        print(f"Followers: {data.get('followers')}")
        print(f"Following: {data.get('following')}")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    get_github_user("octocat")
