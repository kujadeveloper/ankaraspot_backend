from googleapiclient.discovery import build
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from utils.selenium_driver import SeleniumDriver


class Youtube:
    API_KEY = "AIzaSyBdt1jYgL3VEGSoY_pLgG6CadhcolGsu4A"
    YOUTUBE_API_SERVICE_NAME = "youtube"
    YOUTUBE_API_VERSION = "v3"
    youtube = None
    max_results = 1
    driver = None

    def __init__(self):
        self.driver = SeleniumDriver()
        self.youtube = build(self.YOUTUBE_API_SERVICE_NAME, self.YOUTUBE_API_VERSION, developerKey=self.API_KEY)

    def search(self, query):
        try:
            return self.youtube_api(query)
        except Exception as e:
            return self.browser(query)

    def youtube_api(self, query):
        search_response = self.youtube.search().list(
            q=query,
            part="id,snippet",
            maxResults=self.max_results
        ).execute()

        videos = []
        for item in search_response.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                videos.append({"title": title, "id": video_id})

        if len(videos) > 0:
            id = videos[0]['id']
            return f'https://www.youtube.com/embed/{id}'
        else:
            return None

    def browser(self,query):
        driver = self.driver.driver_self(True)
        base_url = 'https://www.youtube.com/results?search_query='
        print(base_url + query.replace(" ", "+").replace('/','-'))
        driver.get(base_url + query.replace(" ", "+"))
        page_source = driver.page_source
        driver.quit()
        # BeautifulSoup ile HTML'yi ayrıştır
        soup = BeautifulSoup(page_source, 'html.parser')
        # İlk video ID'sini bul
        video_links = soup.find_all('a', {'id': 'video-title'})

        for link in video_links:
            if link['href'].startswith('/watch'):
                parsed_url = urlparse(link['href'])
                query_params = parse_qs(parsed_url.query)
                id = query_params.get("v", [None])[0]
                return f'https://www.youtube.com/embed/{id}'

        return None

