from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str:
    parsed_url = urlparse(url)
    
    if parsed_url.netloc in ["youtu.be"]:
        return parsed_url.path.lstrip('/')

    if parsed_url.netloc in ["www.youtube.com", "youtube.com"]:
        return parse_qs(parsed_url.query).get("v", [None])[0]

    return None

# Test case
print(extract_video_id("https://youtu.be/C9X3ok8G4Fs?si=vhtcBjNMR39565Wm"))
# ✅ Output: C9X3ok8G4Fs
