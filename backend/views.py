from django.shortcuts import render
from django.http import JsonResponse
import requests, time, json

def get_data(request):

    # 從請求的獲取參數獲取前端 “keyword” 參數的值
    keyword = request.GET.get('keyword', '')

    # 使用提供的關鍵字構建用於 PCHome 搜索的 URL (請注意 URL 中 &page=? 的部分)
    pchomeUrl = f"https://ecshweb.pchome.com.tw/search/v3.3/all/results?q={keyword}&page=1&sort=rnk/dc"

    # GET請求發送到PCHome並獲取響應文本
    response = requests.get(pchomeUrl).text

    # 暫停執行5秒以避免被blacklist
    # time.sleep(5)

    # 將響應文本解析為 JSON
    data = json.loads(response)

    # 將解析的 JSON 打印到控制台 (請留意 prods 的 label)
    print(data)

    # 返回 data 的 JSON
    return JsonResponse(response, safe=False)