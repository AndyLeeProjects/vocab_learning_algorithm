import requests
from bs4 import BeautifulSoup
import urllib.parse

def scrape_web_images(vocabulary):

    # Perform a web search to get images related to the vocabulary
    query = urllib.parse.quote(vocabulary)
    search_url = f"https://www.google.com/search?q={query}&tbm=isch"

    # Send a GET request to the search URL
    response = requests.get(search_url)
    response.raise_for_status()

    # Parse the HTML content of the response
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all image elements in the HTML
    image_elements = soup.find_all("img")

    # Extract the image URLs from the image elements
    image_urls = [img["src"] for img in image_elements]

    # Choose the first three image URLs
    image_urls = image_urls[1:4]
    
    return image_urls
