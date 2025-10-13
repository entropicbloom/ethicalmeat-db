import subprocess
import json

BASE_URL = "https://www.foodrepo.org/api/v3"
ENDPOINT = "/products"
API_TOKEN = "80c9a5d068965399b54961b132dc72a0"

params = {
    "page[number]": 2,
    "page[size]": 5,
    # examples:
    # "excludes": "images,nutrients",
    # "barcodes": "7610848337010,7610849657797",
}

# Build query string
query_string = "&".join([f"{k}={v}" for k, v in params.items()])
url = f"{BASE_URL}{ENDPOINT}?{query_string}"

# Use curl with --http1.1 to bypass Cloudflare blocking
# This is the exact approach that works from command line
curl_command = [
    "curl",
    "-sS",  # silent but show errors
    "-g",   # disable URL globbing (needed for brackets in query params)
    url,
    "-H", "Accept: application/json",
    "-H", "User-Agent: ethicalmeat-db/0.1 (+you@example.com)",
    "-H", f"Authorization: Token token={API_TOKEN}",
    "--http1.1"
]

result = subprocess.run(curl_command, capture_output=True, text=True)

if result.returncode == 0:
    try:
        data = json.loads(result.stdout)
        print("Status: 200 (success)")
        print("Generated in", data.get("meta", {}).get("generated_in", -1), "ms")
        print("Next page:", data.get("links", {}).get("next"))
        print("Barcodes on this page:")
        for p in data.get("data", []):
            print(" ", p.get("barcode"))
    except json.JSONDecodeError:
        print("Failed to parse JSON response")
        print("Response (first 600 chars):")
        print(result.stdout[:600])
else:
    print(f"Curl failed with return code {result.returncode}")
    print("Error:", result.stderr)
    print("Response (first 600 chars):")
    print(result.stdout[:600])
