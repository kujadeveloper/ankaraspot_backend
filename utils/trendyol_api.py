import requests
import base64


class TrendyolAPI:

    def __init__(self, trendyol_seller_id, trendyol_api_key, trendyol_api_secret):
        self.trendyol_seller_id = trendyol_seller_id
        self.totalcount = 0
        print(trendyol_api_key)
        print(trendyol_api_secret)
        self.headers = {
            'Authorization': f'Basic {base64.b64encode(f"{trendyol_api_key}:{trendyol_api_secret}".encode()).decode()}',
            'Content-Type': 'application/json'
        }

    def get_products(self, page=1):
        url = f'https://api.trendyol.com/sapigw/suppliers/{self.trendyol_seller_id}/products?page={page}'
        print(url)
        response = requests.request("GET", url, headers=self.headers)
        if response.status_code == 200:
            json_data = response.json()
            self.totalcount = json_data['totalElements']
            return json_data
        else:
            return None
