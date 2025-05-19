import requests
from openai import OpenAI




from categories.models import CategoriesModel
class ChatGptApi():
    def __init__(self, prompt):
        self.session = requests.Session()
        self.API_KEY = '*****'
        self.prompt = prompt
        self.client = OpenAI(api_key=self.API_KEY)

    def request_(self):

        prompt = f"Linklerdeki ürünler aynı mı? Fiyat değişikliği gösterebilecek özellikleride baz al. \n\n1. {url1}\n\n2. {url2}\n\nLütfen sadece 'Evet' veya 'Hayır' ile yanıtlayın."
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.API_KEY}"
        }

        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": self.prompt}],
            "max_tokens": 5
        }

        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)

        if response.status_code == 200:
            answer = response.json().choices[0].message.content.strip()
            return answer
        else:
            return f"Error: {response.status_code}, {response.text}"

    def upload_categories_to_chatgpt(self,category_id, category_name):
        from categories.documents import CategoriesDocument
        from elasticsearch_dsl import Q, A
        from categories.serializers import CategoriesSerializer

        must = [
            {"term": {"is_deleted": False}}
        ]
        must_not = [
            Q("exists", field="shop.id")
        ]
        search = CategoriesDocument.search().query("bool", must=must, must_not=must_not, filter=Q("multi_match", query=category_name, fields=['name']))
        response = search.execute()
        if search.count() > 0:
            serializer = CategoriesSerializer(response, many=True).data
            prompt = ''
            for item in serializer:
                prompt += f"- {item['name']}\n"


            #print(prompt)
            prompt_user = f'"{category_name}" bu yukarıdakilerden en uygun olan bir tanesini tam ismini ver. Sadece Yukardaki şıklardan birini yaz.'
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Uygun modeli seçin
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": prompt_user},
                ],
                max_tokens=50  # Tamamlanacak kelime sayısı
            )
            print(prompt)
            print(prompt_user)
            # response = client.completions.create(
            #     model="gpt-3.5-turbo-instruct",  # Uygun modeli seçin
            #     prompt=f'yukardaki listedeki ile en iyi eşleşen sonucu ver. Sadece cevapı tek klime yaz {search}',
            #     max_tokens=5  # Tamamlanacak kelime sayısı
            # )
            answer = response.choices[0].message.content.replace('"', '')
            print(answer)
            try:
                find = CategoriesModel.objects.filter(name=answer, shop__isnull=True).first()
                #print(f'eşleşen {find.name}')
                category = CategoriesModel.objects.filter(id=category_id).first()
                category.match = find
                category.save()
            except:
                print(f'cevap {answer}')
                print(prompt)
                print(prompt_user)
                pass

    def product_match_to_chatgpt(self):
        from categories.documents import CategoriesDocument
        from elasticsearch_dsl import Q, A
        from categories.serializers import CategoriesSerializer
        from products.models import ProductModel


        products = ProductModel.objects.filter(is_deleted=False, match__isnull=False).all()
        print(products.count())
        for product in products:
            all_match = product.match.all()
            links = product.link
            for item in all_match:
                links = f'{links}, {item.link}'
            prompt = links
            prompt_user = f'yukarıdaki linklerde aynı olan ürünlerin liklerini ver'
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",  # Uygun modeli seçin
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": prompt_user},
                ],
                max_tokens=50  # Tamamlanacak kelime sayısı
            )
            print(prompt)
            print(prompt_user)
            answer = response.choices[0].message.content.replace('"', '')
            print(answer)
        #print(prompt)
        #
        # response = self.client.chat.completions.create(
        #     model="gpt-3.5-turbo",  # Uygun modeli seçin
        #     messages=[
        #         {"role": "system", "content": prompt},
        #         {"role": "user", "content": prompt_user},
        #     ],
        #     max_tokens=50  # Tamamlanacak kelime sayısı
        # )
        # print(prompt)
        # print(prompt_user)
        # # response = client.completions.create(
        # #     model="gpt-3.5-turbo-instruct",  # Uygun modeli seçin
        # #     prompt=f'yukardaki listedeki ile en iyi eşleşen sonucu ver. Sadece cevapı tek klime yaz {search}',
        # #     max_tokens=5  # Tamamlanacak kelime sayısı
        # # )
        # answer = response.choices[0].message.content.replace('"', '')
        # print(answer)
        # try:
        #     find = CategoriesModel.objects.filter(name=answer, shop__isnull=True).first()
        #     #print(f'eşleşen {find.name}')
        #     category = CategoriesModel.objects.filter(id=category_id).first()
        #     category.match = find
        #     category.save()
        # except:
        #     print(f'cevap {answer}')
        #     print(prompt)
        #     print(prompt_user)
        #     pass


    def category_match(self, category_name):
        response = openai.completions.create(engine="text-davinci-003",
        prompt=f"Bu kategoriyi eşle: {category_name}",
        temperature=0.7,
        max_tokens=5)