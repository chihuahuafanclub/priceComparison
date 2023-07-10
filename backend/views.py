from django.shortcuts import render
from django.http import JsonResponse
import requests, time, json
from django.views.decorators.csrf import csrf_exempt
from bs4 import BeautifulSoup
import json

@csrf_exempt
def get_data(request):

    keyword = request.GET.get('keyword', '')
    result = []
    count = 0
    page = 1
    while count < 200 :
        pchomeUrl = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={keyword}&page={page}&sort=rnk/dc"
        response = requests.get(pchomeUrl).text
        try:            
            parsed_data = json.loads(response)
            products = parsed_data['prods']
            for product in products:
                name = product['name']
                price = product['price']
                pics = product['picS']
                result.append({'name': name, 'price': price ,'pics': pics})
                count += 1
                if count == 200:
                    break
        except:
            break
        page += 1
    item_count = len(result)
    result.append({'count': item_count})
    
    # 返回 data 的 JSON
    return JsonResponse(json.dumps(result, ensure_ascii=False), safe=False)