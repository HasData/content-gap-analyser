import pandas as pd
import requests
import json

def analyze_entities(text, google_api_key):
    if not text:
        print("[ERROR] No text provided for analysis.")
        return {'error': 'No text provided'}

    url = f'https://language.googleapis.com/v1/documents:analyzeEntities?key={google_api_key}'
    data = {
        "document": {
            "type": "PLAIN_TEXT",
            "content": text
        }
    }

    headers = {
        'Content-Type': 'application/json',
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        print("[INFO] Successfully analyzed entities.")
        return response.json()
    else:
        print(f"[ERROR] Failed to analyze entities. Status Code: {response.status_code}, Error: {response.text}")
        return {'error': response.text}

# Function to extract entity data from the API response, group by name and summarize importance
def get_entities_dataframe(api_response):
    if 'error' in api_response:
        print("[ERROR] API returned an error during entity extraction.")
        return pd.DataFrame(columns=["Entity", "Salience"])

    entities = {}

    for entity in api_response.get('entities', []):
        name = entity.get('name').lower()  # Lowercase the name of the entity
        salience = entity.get('salience')

        # If the entity already exists in the dictionary, summarize salience
        if name in entities:
            entities[name] += salience
        else:
            entities[name] = salience

    if not entities:
        print("[WARNING] No entities found in the analysis.")

    # Create a DataFrame for display
    data = [[name, salience] for name, salience in entities.items()]
    df = pd.DataFrame(data, columns=["Entity", "Salience"])
    return df
