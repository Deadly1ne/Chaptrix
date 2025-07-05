# Site Adapter Implementation Guide

## Introduction

This guide explains how to extend Chaptrix to support additional manga/comic websites by implementing new site adapters. Site adapters are responsible for scraping website data, extracting chapter information, and downloading images.

## Understanding the Adapter Pattern

Chaptrix uses the adapter pattern to provide a consistent interface for different manga/comic websites. Each site adapter must implement the following core functionality:

1. Fetching the latest chapter information
2. Extracting chapter numbers/names
3. Downloading chapter images

## Base Adapter Class

All site adapters extend the `MangaSiteAdapter` base class defined in `main.py`. This class provides the interface that all adapters must implement:

```python
class MangaSiteAdapter:
    """Base class for manga site adapters"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_latest_chapter(self, url):
        """Get the latest chapter information from the manga site"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def extract_chapter_number(self, chapter_text):
        """Extract the chapter number from the chapter text"""
        raise NotImplementedError("Subclasses must implement this method")
    
    def download_chapter_images(self, chapter_url, download_path):
        """Download all images from a chapter"""
        raise NotImplementedError("Subclasses must implement this method")
```

## Implementing a New Site Adapter

To add support for a new manga/comic website, follow these steps:

### 1. Analyze the Target Website

Before writing any code, analyze the website structure:

- How are chapters listed? (HTML structure, JavaScript rendering, etc.)
- How are chapter numbers/names formatted?
- How are images embedded in chapter pages?
- Are there any anti-scraping measures?
- Does the site require authentication?

Use browser developer tools to inspect network requests, HTML structure, and JavaScript behavior.

### 2. Create a New Adapter Class

Create a new class that extends `MangaSiteAdapter`:

```python
class NewSiteAdapter(MangaSiteAdapter):
    """Adapter for example-manga-site.com"""
    
    def get_latest_chapter(self, url):
        """Get the latest chapter information"""
        response = self.session.get(url)
        response.raise_for_status()
        
        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the latest chapter element
        # This will vary depending on the site structure
        latest_chapter_element = soup.select_one('selector-for-latest-chapter')
        
        if not latest_chapter_element:
            return None
        
        # Extract chapter information
        chapter_text = latest_chapter_element.text.strip()
        chapter_url = latest_chapter_element['href']
        if not chapter_url.startswith('http'):
            chapter_url = urljoin(url, chapter_url)
        
        return {
            'chapter': chapter_text,
            'url': chapter_url
        }
    
    def extract_chapter_number(self, chapter_text):
        """Extract the chapter number from the chapter text"""
        # Use regex or string manipulation to extract the number
        match = re.search(r'Chapter (\d+)', chapter_text)
        if match:
            return int(match.group(1))
        return 0
    
    def download_chapter_images(self, chapter_url, download_path):
        """Download all images from a chapter"""
        response = self.session.get(chapter_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all image elements
        # This will vary depending on the site structure
        image_elements = soup.select('selector-for-images')
        
        image_urls = []
        for img in image_elements:
            img_url = img['src']
            if not img_url.startswith('http'):
                img_url = urljoin(chapter_url, img_url)
            image_urls.append(img_url)
        
        # Create download directory if it doesn't exist
        os.makedirs(download_path, exist_ok=True)
        
        # Download each image
        for i, img_url in enumerate(image_urls):
            img_response = self.session.get(img_url)
            img_response.raise_for_status()
            
            # Save the image
            img_path = os.path.join(download_path, f"{i+1}.jpg")
            with open(img_path, 'wb') as f:
                f.write(img_response.content)
            
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        
        return len(image_urls)
```

### 3. Handle Site-Specific Challenges

Different websites present different challenges. Here are some common issues and solutions:

#### JavaScript-Rendered Content

If the website uses JavaScript to load content, you may need to use a headless browser like Selenium or Playwright:

```python
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class JavascriptSiteAdapter(MangaSiteAdapter):
    def __init__(self):
        super().__init__()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def get_latest_chapter(self, url):
        self.driver.get(url)
        
        # Wait for the content to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "selector-for-latest-chapter"))
        )
        
        # Extract chapter information
        latest_chapter_element = self.driver.find_element(By.CSS_SELECTOR, "selector-for-latest-chapter")
        chapter_text = latest_chapter_element.text.strip()
        chapter_url = latest_chapter_element.get_attribute("href")
        
        return {
            'chapter': chapter_text,
            'url': chapter_url
        }
```

#### Authentication

If the website requires authentication:

```python
class AuthenticatedSiteAdapter(MangaSiteAdapter):
    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.login()
    
    def login(self):
        login_url = "https://example-manga-site.com/login"
        login_data = {
            "username": self.username,
            "password": self.password
        }
        response = self.session.post(login_url, data=login_data)
        response.raise_for_status()
        
        # Check if login was successful
        if "Login failed" in response.text:
            raise Exception("Login failed. Check your credentials.")
```

#### Anti-Scraping Measures

If the website has anti-scraping measures:

```python
class ProtectedSiteAdapter(MangaSiteAdapter):
    def __init__(self):
        super().__init__()
        # Add additional headers to mimic a browser
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
            "TE": "Trailers"
        })
    
    def get_latest_chapter(self, url):
        # Add random delay to avoid detection
        time.sleep(random.uniform(1, 3))
        
        # Use a proxy if needed
        proxies = {
            "http": "http://proxy-server:port",
            "https": "https://proxy-server:port"
        }
        response = self.session.get(url, proxies=proxies)
        # Rest of the implementation
```

### 4. Register the New Adapter

Add your new adapter to the `get_site_adapter` function in `main.py`:

```python
def get_site_adapter(site_name):
    """Get the appropriate site adapter based on the site name"""
    adapters = {
        "baozimh": BaozimhAdapter,
        "newsite": NewSiteAdapter  # Add your new adapter here
    }
    
    adapter_class = adapters.get(site_name)
    if not adapter_class:
        raise ValueError(f"Unsupported site: {site_name}")
    
    return adapter_class()
```

### 5. Test Your Adapter

Create a test script to verify your adapter works correctly:

```python
def test_new_adapter():
    adapter = NewSiteAdapter()
    test_url = "https://example-manga-site.com/manga/test-manga"
    
    # Test getting latest chapter
    latest_chapter = adapter.get_latest_chapter(test_url)
    print(f"Latest chapter: {latest_chapter}")
    
    # Test extracting chapter number
    chapter_number = adapter.extract_chapter_number(latest_chapter['chapter'])
    print(f"Chapter number: {chapter_number}")
    
    # Test downloading images
    download_path = os.path.join("downloads", "test_adapter")
    image_count = adapter.download_chapter_images(latest_chapter['url'], download_path)
    print(f"Downloaded {image_count} images to {download_path}")

if __name__ == "__main__":
    test_new_adapter()
```

## Best Practices

### 1. Respect Website Terms of Service

Before implementing a scraper, check the website's terms of service and robots.txt file to ensure scraping is allowed.

### 2. Be Gentle with Requests

Implement rate limiting to avoid overloading the website:

```python
def download_chapter_images(self, chapter_url, download_path):
    # Implementation
    for i, img_url in enumerate(image_urls):
        # Download image
        # ...
        
        # Add a delay between requests
        time.sleep(random.uniform(0.5, 2.0))
```

### 3. Handle Errors Gracefully

Implement robust error handling:

```python
def get_latest_chapter(self, url):
    try:
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        # Rest of implementation
    except requests.exceptions.Timeout:
        logging.error(f"Timeout while accessing {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error while accessing {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while accessing {url}: {e}")
        return None
```

### 4. Document Your Adapter

Add comprehensive documentation to your adapter:

```python
class NewSiteAdapter(MangaSiteAdapter):
    """Adapter for example-manga-site.com
    
    This adapter supports scraping manga chapters from example-manga-site.com.
    
    Notes:
        - The site uses a standard HTML structure with no JavaScript rendering
        - Chapter URLs follow the pattern: /manga/{manga-name}/chapter-{number}
        - Images are stored in standard <img> tags within a .chapter-content div
    """
```

## Example: Implementing a MangaDex Adapter

Here's a simplified example of how to implement an adapter for MangaDex:

```python
class MangaDexAdapter(MangaSiteAdapter):
    """Adapter for MangaDex"""
    
    def __init__(self):
        super().__init__()
        self.api_base_url = "https://api.mangadex.org"
    
    def get_latest_chapter(self, manga_url):
        # Extract manga ID from URL
        manga_id = manga_url.split("/")[-1]
        
        # Get chapters via API
        params = {
            "manga": manga_id,
            "translatedLanguage[]": ["en"],
            "order[chapter]": "desc",
            "limit": 1
        }
        response = self.session.get(f"{self.api_base_url}/chapter", params=params)
        response.raise_for_status()
        
        data = response.json()
        if not data["data"]:
            return None
        
        chapter_data = data["data"][0]
        chapter_id = chapter_data["id"]
        chapter_num = chapter_data["attributes"]["chapter"]
        chapter_title = chapter_data["attributes"]["title"]
        
        chapter_text = f"Chapter {chapter_num}"
        if chapter_title:
            chapter_text += f": {chapter_title}"
        
        return {
            "chapter": chapter_text,
            "url": f"https://mangadex.org/chapter/{chapter_id}",
            "id": chapter_id
        }
    
    def extract_chapter_number(self, chapter_text):
        match = re.search(r'Chapter (\d+)', chapter_text)
        if match:
            return float(match.group(1))
        return 0
    
    def download_chapter_images(self, chapter_url, download_path):
        # Extract chapter ID from URL
        chapter_id = chapter_url.split("/")[-1]
        
        # Get chapter data
        response = self.session.get(f"{self.api_base_url}/chapter/{chapter_id}")
        response.raise_for_status()
        chapter_data = response.json()["data"]
        
        # Get server and hash information
        response = self.session.get(
            f"{self.api_base_url}/at-home/server/{chapter_id}"
        )
        response.raise_for_status()
        server_data = response.json()
        
        base_url = server_data["baseUrl"]
        chapter_hash = server_data["chapter"]["hash"]
        file_names = server_data["chapter"]["data"]
        
        # Create download directory
        os.makedirs(download_path, exist_ok=True)
        
        # Download each image
        for i, file_name in enumerate(file_names):
            img_url = f"{base_url}/data/{chapter_hash}/{file_name}"
            img_response = self.session.get(img_url)
            img_response.raise_for_status()
            
            img_path = os.path.join(download_path, f"{i+1}.jpg")
            with open(img_path, 'wb') as f:
                f.write(img_response.content)
            
            # Add a delay to avoid rate limiting
            time.sleep(0.5)
        
        return len(file_names)
```

## Conclusion

By following this guide, you can extend Chaptrix to support additional manga/comic websites. Remember to respect website terms of service, implement rate limiting, and handle errors gracefully.

If you implement a new site adapter, consider contributing it back to the Chaptrix project to benefit other users.