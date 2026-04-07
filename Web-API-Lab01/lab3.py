import requests
from requests.exceptions import HTTPError, Timeout, RequestException

def get_json(url):
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        print("Success")
    except Timeout:
        # Expected: Error: request timeout
        print("Error: request timeout")
    except HTTPError as e:
        status_code = e.response.status_code
        if status_code == 404:
            # Expected: Error: 404 Not Found
            print("Error: 404 Not Found")
        elif status_code == 500:
            # Expected: Error: server problem
            print("Error: server problem")
        else:
            print(f"Error: {status_code}")
    except RequestException:
        print("Error: request error")

if __name__ == "__main__":
    # URL สำหรับทดสอบจาก PDF
    test_urls = [
        "https://httpbin.org/status/404",
        "https://httpbin.org/status/500",
        "https://httpbin.org/delay/10",
        "https://api.github.com/users/octocat"
    ]
    
    for url in test_urls:
        print(f"Testing URL: {url}")
        get_json(url)
        print("-" * 20)
