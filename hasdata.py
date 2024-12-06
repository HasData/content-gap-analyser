import json
import requests
from newspaper import Article

def extract_html_via_api(url, hasdata_api_key):
    # Send a request to the API to get the HTML content
    api_url = "https://api.hasdata.com/scrape/web"
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': hasdata_api_key
    }
    data = {
        "url": url,
        "proxyType": "residential",
        "proxyCountry": "US",
        "blockResources": False,
        "blockAds": False,
        "screenshot": False,
        "jsRendering": True,
        "excludeHtml": False,
        "extractEmails": False
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        html_content = response_json.get('content')
        if html_content:
            print(f"[INFO] HTML content successfully extracted for URL: {url}")
        else:
            print(f"[WARNING] No HTML content extracted for URL: {url}")
        return html_content
    else:
        print(f"[ERROR] Failed to extract HTML content for URL: {url}, Status Code: {response.status_code}")
        return None

def extract_text_from_html(html_content):
    try:
        article = Article('')
        article.set_html(html_content)
        article.parse()
        print("[INFO] Successfully parsed article text.")
        return article.text
    except Exception as e:
        print(f"[ERROR] Failed to parse article text. Error: {e}")
        return None

def extract_serp_via_api(keyword, hasdata_api_key):
    # Send a request to the API to get the HTML content
    api_url = "https://api.hasdata.com/scrape/google/serp"
    headers = {
        'Content-Type': 'application/json',
        'x-api-key': hasdata_api_key
    }
    data = {
        "q": keyword
    }

    response = requests.post(api_url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        response_json = response.json()
        organic_results = response_json.get('organicResults')
        if organic_results:
            print(f"[INFO] SERP results successfully extracted for keyword: {keyword}")
        else:
            print(f"[WARNING] No SERP results for keyword: {keyword}")
        return organic_results
    else:
        print(f"[ERROR] Failed to extract SERP results for keyword: {keyword}, Status Code: {response.status_code}")
        return None
