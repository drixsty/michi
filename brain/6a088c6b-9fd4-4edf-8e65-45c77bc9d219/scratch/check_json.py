import json
from collections import Counter

def find_duplicates(obj, path=""):
    if isinstance(obj, dict):
        keys = list(obj.keys())
        duplicates = [k for k, count in Counter(keys).items() if count > 1]
        for k in duplicates:
            print(f"Duplicate key: {path}.{k}")
        for k, v in obj.items():
            find_duplicates(v, f"{path}.{k}")

files = [
    r"c:\Users\KevinTSAGUE\michi-app\apps\landing\messages\fr.json",
    r"c:\Users\KevinTSAGUE\michi-app\apps\landing\messages\en.json"
]

for f in files:
    print(f"Checking {f}...")
    try:
        with open(f, 'r', encoding='utf-8') as file:
            # Note: json.load doesn't allow duplicate keys by default, 
            # it just overwrites them. To find them, we need a custom decoder.
            pass
    except Exception as e:
        print(f"Error: {e}")

# Revised strategy: search for exact string matches of keys
