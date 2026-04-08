import requests
import os

url = "http://localhost:5001/api/graph/ontology/generate"
project_name = "Debug Project"
simulation_requirement = "Analyze social simulation patterns"

# Create a small dummy file
dummy_file_path = "debug_text.txt"
with open(dummy_file_path, "w", encoding="utf-8") as f:
    f.write("Aarambh is a social simulation engine. It uses knowledge graphs to simulate interactions between people and organizations.")

files = [
    ('files', (dummy_file_path, open(dummy_file_path, 'rb'), 'text/plain'))
]

data = {
    'project_name': project_name,
    'simulation_requirement': simulation_requirement
}

print(f"Calling {url}...")
try:
    response = requests.post(url, data=data, files=files)
    print(f"Status Code: {response.status_code}")
    print("Response JSON:")
    try:
        import json
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)
except Exception as e:
    print(f"Request failed: {str(e)}")
finally:
    # Cleanup dummy file
    for _, (path, f, _) in files:
        f.close()
    if os.path.exists(dummy_file_path):
        os.remove(dummy_file_path)
