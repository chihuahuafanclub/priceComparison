import json
import os
import re
from html import unescape
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import parse_qs
from urllib.parse import quote
from urllib.parse import unquote
from urllib.parse import urlparse

import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET

PCHOME_SEARCH_URL = "https://ecshweb.pchome.com.tw/search/v3.3/all/results"
PCHOME_IMAGE_HOST = "https://cs-a.ecimg.tw"

RUTEN_SEARCH_URL = "https://rtapi.ruten.com.tw/api/search/v3/index.php/core/prod"
RUTEN_PRODUCT_URL = "https://rtapi.ruten.com.tw/api/prod/v2/index.php/prod"
RUTEN_IMAGE_HOST = "https://gcs.rimg.com.tw"

MOMO_SEARCH_URL_TEMPLATE = "https://www.momoshop.com.tw/search/{keyword}?viewport=desktop"

YAHOO_SEARCH_URL = "https://tw.buy.yahoo.com/search/product"

SHOPEE_SEARCH_URL = "https://shopee.tw/api/v4/search/search_items/"

TAOBAO_SEARCH_URL = "https://s.taobao.com/search"

SORT_OPTIONS = {"relevance", "price_asc", "price_desc"}
AVAILABLE_PROVIDERS = (
    "pchome",
    "ruten",
    "momo",
    "yahoo",
    "shopee",
    "taobao",
)

DEFAULT_LIMIT = 24
MAX_LIMIT = 120
REQUEST_TIMEOUT_SECONDS = 10
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
}

IN_STOCK_STATUS_TOKENS = {
    "1",
    "true",
    "on",
    "onshelf",
    "on_shelf",
    "online",
    "active",
    "normal",
    "available",
    "in_stock",
    "instock",
    "sale",
    "onsale",
    "on_sale",
}
OUT_OF_STOCK_STATUS_TOKENS = {
    "0",
    "false",
    "off",
    "offline",
    "off_shelf",
    "offshelf",
    "inactive",
    "disabled",
    "disable",
    "soldout",
    "sold_out",
    "out",
    "outofstock",
    "out_of_stock",
    "unavailable",
    "deleted",
    "ban",
}
IN_STOCK_SIGNAL_TERMS = (
    "現貨",
    "可購買",
    "可下單",
    "有庫存",
    "立即出貨",
    "in stock",
    "available",
)
OUT_OF_STOCK_SIGNAL_TERMS = (
    "下架",
    "停售",
    "停賣",
    "售完",
    "售罄",
    "缺貨",
    "補貨中",
    "無庫存",
    "out of stock",
    "sold out",
    "not available",
    "unavailable",
)

ENABLE_BROWSER_FALLBACK = str(os.getenv("ENABLE_BROWSER_FALLBACK", "0")).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
BROWSER_CHANNEL = str(os.getenv("BROWSER_CHANNEL", "msedge")).strip() or "msedge"
BROWSER_USER_DATA_DIR = str(os.getenv("BROWSER_USER_DATA_DIR", "")).strip()
BROWSER_HEADLESS = str(os.getenv("BROWSER_HEADLESS", "1")).strip().lower() in {"1", "true", "yes", "on"}
try:
    BROWSER_TIMEOUT_MS = int(str(os.getenv("BROWSER_TIMEOUT_MS", "45000")).strip())
except ValueError:
    BROWSER_TIMEOUT_MS = 45000

def _safe_int(value: Any, default: int, min_value: int = 1, max_value: Optional[int] = None) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    if parsed < min_value:
        return min_value
    if max_value is not None and parsed > max_value:
        return max_value
    return parsed


def _safe_price(value: Any) -> Optional[int]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        parsed = int(value)
        return parsed if parsed >= 0 else None

    text = str(value).strip()
    if not text:
        return None

    decimal_candidate = text.replace(",", "")
    if re.fullmatch(r"\d+(\.\d+)?", decimal_candidate):
        parsed_decimal = int(float(decimal_candidate))
        return parsed_decimal if parsed_decimal >= 0 else None

    digits = re.sub(r"[^0-9]", "", text)
    if not digits:
        return None

    parsed = int(digits)
    return parsed if parsed >= 0 else None


def _first_non_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().replace(",", "")
    if not text:
        return None

    matched = re.search(r"-?\d+(\.\d+)?", text)
    if not matched:
        return None

    try:
        return float(matched.group(0))
    except ValueError:
        return None


def _parse_tags(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        tags = [str(item).strip() for item in value if str(item).strip()]
        return tags[:8]
    if isinstance(value, str):
        candidates = re.split(r"[,|/;、\s]+", value)
        tags = [item.strip() for item in candidates if item.strip()]
        return tags[:8]
    return []


def _normalize_status_token(value: Any) -> str:
    token = str(value or "").strip().lower()
    if not token:
        return ""
    token = token.replace("-", "_").replace(" ", "_")
    return token


def _explicit_availability(value: Any) -> Optional[str]:
    token = _normalize_status_token(value)
    if not token:
        return None
    if token in IN_STOCK_STATUS_TOKENS:
        return "in_stock"
    if token in OUT_OF_STOCK_STATUS_TOKENS:
        return "out_of_stock"
    return None


def _match_signal_terms(text_sources: List[Any], terms: Tuple[str, ...]) -> List[str]:
    merged_text = " ".join(_decode_escaped(item).lower() for item in text_sources if item is not None)
    if not merged_text:
        return []
    matched = [term for term in terms if term in merged_text]
    return matched[:3]


def _resolve_availability(
    *,
    explicit_status: Optional[str] = None,
    stock_qty: Optional[int] = None,
    text_sources: Optional[List[Any]] = None,
    default_if_unknown: str = "unknown",
) -> Tuple[str, str, List[str]]:
    signals: List[str] = []
    normalized_explicit = explicit_status if explicit_status in {"in_stock", "out_of_stock"} else None

    if normalized_explicit:
        signals.append(f"explicit_status:{normalized_explicit}")

    if stock_qty is not None:
        signals.append("stock_qty>0" if stock_qty > 0 else "stock_qty<=0")

    safe_text_sources = text_sources or []
    positive_terms = _match_signal_terms(safe_text_sources, IN_STOCK_SIGNAL_TERMS)
    negative_terms = _match_signal_terms(safe_text_sources, OUT_OF_STOCK_SIGNAL_TERMS)
    if positive_terms:
        signals.append(f"positive_terms:{'|'.join(positive_terms)}")
    if negative_terms:
        signals.append(f"negative_terms:{'|'.join(negative_terms)}")

    status = "unknown"
    if normalized_explicit == "out_of_stock" or (stock_qty is not None and stock_qty <= 0) or negative_terms:
        status = "out_of_stock"
    elif normalized_explicit == "in_stock" or (stock_qty is not None and stock_qty > 0) or positive_terms:
        status = "in_stock"
    elif default_if_unknown in {"in_stock", "out_of_stock", "unknown"}:
        status = default_if_unknown

    if normalized_explicit or stock_qty is not None:
        confidence = "high"
    elif positive_terms or negative_terms:
        confidence = "medium"
    else:
        confidence = "low"

    return status, confidence, signals[:5]


def _availability_text(status: str) -> str:
    if status == "in_stock":
        return "可購買"
    if status == "out_of_stock":
        return "疑似下架/缺貨"
    return "狀態未知"


def _decode_escaped(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    if "\\u" in text or "\\/" in text:
        try:
            text = text.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            pass

    return unescape(text.replace("\\/", "/").replace("\\u0026", "&"))


def _normalize_image_url(image_url: Any, base_url: Optional[str] = None) -> str:
    value = _decode_escaped(image_url)
    if not value or value.lower() == "none":
        return ""

    if value.startswith("//"):
        return f"https:{value}"

    if value.startswith("/"):
        if base_url:
            return f"{base_url.rstrip('/')}{value}"
        return ""

    if value.startswith("http://") or value.startswith("https://"):
        return value

    if base_url:
        return f"{base_url.rstrip('/')}/{value.lstrip('/')}"

    return value


def _paginate_items(items: List[Dict[str, Any]], page: int, per_page: int) -> List[Dict[str, Any]]:
    start = max(page - 1, 0) * per_page
    end = start + per_page
    return items[start:end]


def _parse_providers(raw_value: str) -> List[str]:
    if not raw_value or raw_value.strip().lower() == "all":
        return list(AVAILABLE_PROVIDERS)

    providers: List[str] = []
    for candidate in raw_value.split(","):
        provider = candidate.strip().lower()
        if provider in AVAILABLE_PROVIDERS and provider not in providers:
            providers.append(provider)

    return providers or list(AVAILABLE_PROVIDERS)


def _normalize_common_item(
    *,
    product_id: str,
    source: str,
    title: str,
    price: Optional[int],
    original_price: Optional[int],
    image_url: str,
    product_url: str,
    availability: str = "unknown",
    availability_confidence: str = "low",
    availability_signals: Optional[List[str]] = None,
    stock_qty: Optional[int] = None,
    shop_name: str = "",
    sales_count: Optional[int] = None,
    rating: Optional[float] = None,
    review_count: Optional[int] = None,
    shipping_text: str = "",
    location: str = "",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    normalized_tags = tags or []
    availability_state = availability if availability in {"in_stock", "out_of_stock", "unknown"} else "unknown"
    normalized_confidence = (
        availability_confidence
        if availability_confidence in {"high", "medium", "low"}
        else ("high" if availability_state != "unknown" else "low")
    )
    normalized_signals = [str(item).strip() for item in (availability_signals or []) if str(item).strip()][:5]

    return {
        "id": product_id,
        "source": source,
        "title": title,
        "price": price,
        "original_price": original_price,
        "discount_amount": (original_price - price) if price is not None and original_price is not None else None,
        "image_url": image_url,
        "product_url": product_url,
        "availability": availability_state,
        "availability_text": _availability_text(availability_state),
        "availability_confidence": normalized_confidence,
        "availability_signals": normalized_signals,
        "is_available": True if availability_state == "in_stock" else (False if availability_state == "out_of_stock" else None),
        "is_off_shelf": availability_state == "out_of_stock",
        "stock_qty": stock_qty,
        "shop_name": shop_name,
        "sales_count": sales_count,
        "rating": rating,
        "review_count": review_count,
        "shipping_text": shipping_text,
        "location": location,
        "tags": normalized_tags,
    }


def _normalize_pchome_item(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    product_id = str(raw_item.get("Id") or raw_item.get("id") or "").strip()
    title = str(raw_item.get("name") or raw_item.get("Name") or "").strip()
    if not product_id or not title:
        return None

    price = _safe_price(raw_item.get("price"))
    original_price = _safe_price(raw_item.get("originPrice"))
    image_url = _normalize_image_url(raw_item.get("picB") or raw_item.get("picS"), PCHOME_IMAGE_HOST)
    tags = _parse_tags(raw_item.get("brand"))
    stock_qty = _safe_price(_first_non_none(raw_item.get("Qty"), raw_item.get("qty"), raw_item.get("stock")))
    explicit_status = (
        _explicit_availability(raw_item.get("isSale"))
        or _explicit_availability(raw_item.get("sellStatus"))
        or _explicit_availability(raw_item.get("status"))
        or _explicit_availability(raw_item.get("buttonType"))
    )
    availability, availability_confidence, availability_signals = _resolve_availability(
        explicit_status=explicit_status,
        stock_qty=stock_qty,
        text_sources=[
            title,
            raw_item.get("Describe"),
            raw_item.get("buttonType"),
            raw_item.get("msg"),
            raw_item.get("state"),
        ],
        default_if_unknown="in_stock" if price is not None else "unknown",
    )

    return _normalize_common_item(
        product_id=product_id,
        source="PChome 24h購物",
        title=title,
        price=price,
        original_price=original_price,
        image_url=image_url,
        product_url=f"https://24h.pchome.com.tw/prod/{product_id}",
        availability=availability,
        availability_confidence=availability_confidence,
        availability_signals=availability_signals,
        stock_qty=stock_qty,
        shop_name="PChome 24h購物",
        tags=tags,
    )


def _normalize_ruten_item(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    product_id = str(raw_item.get("ProdId") or "").strip()
    title = str(raw_item.get("ProdName") or "").strip()
    if not product_id or not title:
        return None

    price_range = raw_item.get("PriceRange")
    min_price: Optional[int] = None
    max_price: Optional[int] = None

    if isinstance(price_range, list) and price_range:
        min_price = _safe_price(price_range[0])
        if len(price_range) > 1:
            max_price = _safe_price(price_range[1])

    image_url = _normalize_image_url(raw_item.get("Image"), RUTEN_IMAGE_HOST)
    stock_qty = _safe_price(raw_item.get("StockQty"))
    stock_status = str(raw_item.get("StockStatus") or "").strip().lower()
    explicit_status = _explicit_availability(stock_status) or _explicit_availability(raw_item.get("Status"))
    availability, availability_confidence, availability_signals = _resolve_availability(
        explicit_status=explicit_status,
        stock_qty=stock_qty,
        text_sources=[
            title,
            stock_status,
            raw_item.get("ProdStatus"),
            raw_item.get("ProdDesc"),
        ],
        default_if_unknown="in_stock" if min_price is not None else "unknown",
    )

    shipping_cost = _safe_price(raw_item.get("ShippingCost"))
    shipping_text = "免運" if shipping_cost == 0 else (f"運費 {shipping_cost}" if shipping_cost is not None else "")
    tags = _parse_tags(raw_item.get("SaleType"))
    deliver_way = raw_item.get("DeliverWay")
    if isinstance(deliver_way, list):
        tags.extend(_parse_tags(deliver_way))
    seller_id = str(raw_item.get("SellerId") or "").strip()
    sales_count = _safe_price(raw_item.get("SoldQty"))

    return _normalize_common_item(
        product_id=product_id,
        source="露天拍賣",
        title=title,
        price=min_price,
        original_price=max_price if max_price is not None and min_price is not None and max_price > min_price else None,
        image_url=image_url,
        product_url=f"https://www.ruten.com.tw/item/show?{product_id}",
        availability=availability,
        availability_confidence=availability_confidence,
        availability_signals=availability_signals,
        stock_qty=stock_qty,
        shop_name=f"露天賣家 {seller_id}" if seller_id else "露天拍賣",
        sales_count=sales_count,
        shipping_text=shipping_text,
        tags=tags[:8],
    )


def _normalize_momo_item(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    product_id = str(raw_item.get("goodsCode") or "").strip()
    title = _decode_escaped(raw_item.get("goodsName"))
    if not product_id or not title:
        return None

    price = _safe_price(_first_non_none(raw_item.get("SALE_PRICE"), raw_item.get("goodsPrice")))
    original_price = _safe_price(raw_item.get("goodsPriceOri"))
    image_url = _normalize_image_url(raw_item.get("imgUrl"))
    product_url = _decode_escaped(raw_item.get("goodsUrl"))
    stock_qty = _safe_price(raw_item.get("goodsStock"))
    goods_status = str(raw_item.get("goodsStatus") or "").strip().lower()
    explicit_status = _explicit_availability(goods_status)
    availability, availability_confidence, availability_signals = _resolve_availability(
        explicit_status=explicit_status,
        stock_qty=stock_qty,
        text_sources=[
            title,
            goods_status,
            raw_item.get("onSaleDescription"),
            raw_item.get("shopWay"),
            raw_item.get("goodsDescribe"),
        ],
        default_if_unknown="in_stock" if price is not None else "unknown",
    )

    rating = _safe_float(raw_item.get("rating"))
    review_count = _safe_price(raw_item.get("ratingTimes"))
    shipping_text = _decode_escaped(raw_item.get("shopWay") or raw_item.get("onSaleDescription"))
    tags = _parse_tags(raw_item.get("goodsFeatureUrl"))

    if not product_url:
        product_url = f"https://www.momoshop.com.tw/goods/GoodsDetail.jsp?i_code={product_id}"

    return _normalize_common_item(
        product_id=product_id,
        source="momo購物網",
        title=title,
        price=price,
        original_price=original_price,
        image_url=image_url,
        product_url=product_url,
        availability=availability,
        availability_confidence=availability_confidence,
        availability_signals=availability_signals,
        stock_qty=stock_qty,
        shop_name="momo購物網",
        rating=rating,
        review_count=review_count,
        shipping_text=shipping_text,
        tags=tags,
    )


def _normalize_yahoo_item(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    product_id = str(raw_item.get("ec_productid") or raw_item.get("ec_productno") or "").strip()
    title = _decode_escaped(raw_item.get("ec_title"))
    if not product_id or not title:
        return None

    price = _safe_price(raw_item.get("ec_price"))
    original_price = _safe_price(raw_item.get("ec_listprice"))
    image_url = _normalize_image_url(raw_item.get("ec_image"))
    product_url = _decode_escaped(raw_item.get("ec_item_url"))
    if not product_url:
        return None

    stock_qty = _safe_price(raw_item.get("ec_stockcount"))
    has_stock = raw_item.get("ec_has_stock")
    shelf_status = str(raw_item.get("ec_shelf_status") or raw_item.get("ec_status") or "").strip().lower()
    explicit_status = _explicit_availability(shelf_status)
    if isinstance(has_stock, bool):
        explicit_status = "in_stock" if has_stock else "out_of_stock"
    availability, availability_confidence, availability_signals = _resolve_availability(
        explicit_status=explicit_status,
        stock_qty=stock_qty,
        text_sources=[
            title,
            shelf_status,
            raw_item.get("ec_promotext"),
            raw_item.get("ec_stock_note"),
            raw_item.get("ec_badge"),
        ],
        default_if_unknown="in_stock" if price is not None else "unknown",
    )

    sales_count = _safe_price(raw_item.get("ec_total_sales_count") or raw_item.get("ec_sales_count"))
    rating = _safe_float(raw_item.get("ec_global_rating"))
    review_count = _safe_price(raw_item.get("ec_rating_count"))
    shop_name = _decode_escaped(raw_item.get("ec_storename") or raw_item.get("ec_seller"))
    shipping_text = _decode_escaped(raw_item.get("ec_delivertype") or raw_item.get("ec_delvtype"))
    location = _decode_escaped(raw_item.get("ec_realsubstationarea"))
    tags = _parse_tags(raw_item.get("ec_filtertags") or raw_item.get("ec_product_tags") or raw_item.get("ec_brand"))

    return _normalize_common_item(
        product_id=product_id,
        source="Yahoo購物中心",
        title=title,
        price=price,
        original_price=original_price,
        image_url=image_url,
        product_url=product_url,
        availability=availability,
        availability_confidence=availability_confidence,
        availability_signals=availability_signals,
        stock_qty=stock_qty,
        shop_name=shop_name,
        sales_count=sales_count,
        rating=rating,
        review_count=review_count,
        shipping_text=shipping_text,
        location=location,
        tags=tags,
    )


def _normalize_shopee_item(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    item_basic = raw_item.get("item_basic") if isinstance(raw_item, dict) else None
    payload = item_basic if isinstance(item_basic, dict) else raw_item

    item_id = str(payload.get("itemid") or payload.get("item_id") or "").strip()
    shop_id = str(payload.get("shopid") or payload.get("shop_id") or "").strip()
    title = _decode_escaped(payload.get("name"))

    if not item_id or not shop_id or not title:
        return None

    raw_price = payload.get("price")
    price = _safe_price(raw_price)
    if price is not None and price > 1_000_000:
        price = int(price / 100000)

    raw_original = payload.get("price_before_discount")
    original_price = _safe_price(raw_original)
    if original_price is not None and original_price > 1_000_000:
        original_price = int(original_price / 100000)

    image_id = str(payload.get("image") or "").strip()
    image_url = f"https://down-tw.img.susercontent.com/file/{image_id}" if image_id else ""
    stock_qty = _safe_price(payload.get("stock"))
    status_raw = str(payload.get("item_status") or payload.get("status") or "").strip().lower()
    explicit_status = _explicit_availability(status_raw)
    availability, availability_confidence, availability_signals = _resolve_availability(
        explicit_status=explicit_status,
        stock_qty=stock_qty,
        text_sources=[
            title,
            status_raw,
            payload.get("status_reason"),
        ],
        default_if_unknown="in_stock" if price is not None else "unknown",
    )

    sales_count = _safe_price(payload.get("historical_sold") or payload.get("sold"))
    rating_data = payload.get("item_rating")
    rating: Optional[float] = None
    review_count: Optional[int] = None
    if isinstance(rating_data, dict):
        rating = _safe_float(rating_data.get("rating_star"))
        raw_counts = rating_data.get("rating_count")
        if isinstance(raw_counts, list) and raw_counts:
            review_count = sum(_safe_price(item) or 0 for item in raw_counts[1:]) if len(raw_counts) > 1 else _safe_price(raw_counts[0])
    shop_name = _decode_escaped(payload.get("shop_name") or "")
    location = _decode_escaped(payload.get("shop_location") or "")
    tags = _parse_tags(payload.get("label_ids"))

    return _normalize_common_item(
        product_id=f"{shop_id}_{item_id}",
        source="蝦皮購物",
        title=title,
        price=price,
        original_price=original_price,
        image_url=image_url,
        product_url=f"https://shopee.tw/product/{shop_id}/{item_id}",
        availability=availability,
        availability_confidence=availability_confidence,
        availability_signals=availability_signals,
        stock_qty=stock_qty,
        shop_name=shop_name or f"蝦皮店家 {shop_id}",
        sales_count=sales_count,
        rating=rating,
        review_count=review_count,
        location=location,
        tags=tags,
    )


def _parse_jsonp_payload(raw_text: str) -> Optional[Dict[str, Any]]:
    text = str(raw_text or "").strip()
    if not text:
        return None

    matched = re.search(r"^[^(]+\(([\s\S]+)\)\s*;?\s*$", text)
    if not matched:
        return None

    try:
        payload = json.loads(matched.group(1))
    except json.JSONDecodeError:
        return None

    return payload if isinstance(payload, dict) else None


def _open_playwright_context(playwright):
    if BROWSER_USER_DATA_DIR:
        context = playwright.chromium.launch_persistent_context(
            BROWSER_USER_DATA_DIR,
            channel=BROWSER_CHANNEL,
            headless=BROWSER_HEADLESS,
        )
        return None, context

    browser = playwright.chromium.launch(channel=BROWSER_CHANNEL, headless=BROWSER_HEADLESS)
    context = browser.new_context()
    return browser, context


def _extract_taobao_items_from_node(node: Any, bucket: List[Dict[str, Any]]) -> None:
    if isinstance(node, dict):
        item_id = str(node.get("itemId") or node.get("item_id") or node.get("nid") or "").strip()
        title = _decode_escaped(
            node.get("title")
            or node.get("raw_title")
            or node.get("itemTitle")
            or node.get("item_name")
            or ""
        )
        price = _safe_price(
            _first_non_none(
                node.get("price"),
                node.get("view_price"),
                node.get("itemPrice"),
                node.get("promotionPrice"),
                node.get("currentPrice"),
            )
        )
        image_url = _normalize_image_url(
            node.get("picPath")
            or node.get("pic_url")
            or node.get("image")
            or node.get("imageUrl")
            or ""
        )
        product_url = _decode_escaped(
            node.get("itemUrl")
            or node.get("detailUrl")
            or node.get("url")
            or ""
        )
        if product_url.startswith("//"):
            product_url = f"https:{product_url}"

        if item_id and title and price is not None:
            stock_qty = _safe_price(_first_non_none(node.get("stock"), node.get("stockQty")))
            status_raw = str(node.get("itemStatus") or node.get("status") or "").strip().lower()
            explicit_status = _explicit_availability(status_raw)
            availability, availability_confidence, availability_signals = _resolve_availability(
                explicit_status=explicit_status,
                stock_qty=stock_qty,
                text_sources=[
                    title,
                    status_raw,
                    node.get("statusText"),
                    node.get("description"),
                ],
                default_if_unknown="in_stock",
            )

            sales_count = _safe_price(node.get("sold") or node.get("sales") or node.get("sellCount"))
            shop_name = _decode_escaped(node.get("shopTitle") or node.get("sellerName") or "")
            location = _decode_escaped(node.get("location") or node.get("itemLoc") or "")
            tags = _parse_tags(node.get("icons") or node.get("property"))

            if not product_url:
                product_url = f"https://item.taobao.com/item.htm?id={item_id}"

            bucket.append(
                _normalize_common_item(
                    product_id=item_id,
                    source="淘寶",
                    title=title,
                    price=price,
                    original_price=None,
                    image_url=image_url,
                    product_url=product_url,
                    availability=availability,
                    availability_confidence=availability_confidence,
                    availability_signals=availability_signals,
                    stock_qty=stock_qty,
                    shop_name=shop_name,
                    sales_count=sales_count,
                    location=location,
                    tags=tags,
                )
            )

        for value in node.values():
            _extract_taobao_items_from_node(value, bucket)
    elif isinstance(node, list):
        for item in node:
            _extract_taobao_items_from_node(item, bucket)


def _fetch_shopee_products_with_browser(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return [], ["蝦皮瀏覽器備援無法啟用（缺少 Playwright）。"]

    newest = (page - 1) * fetch_limit
    api_params = {
        "by": "relevancy",
        "keyword": keyword,
        "limit": fetch_limit,
        "newest": newest,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2,
    }
    expected_keys = {str(k): str(v) for k, v in api_params.items()}
    captured_payloads: List[Dict[str, Any]] = []

    try:
        with sync_playwright() as playwright:
            browser, context = _open_playwright_context(playwright)
            page_obj = context.new_page()

            def on_response(response):
                try:
                    parsed = urlparse(response.url)
                    if "/api/v4/search/search_items" not in parsed.path:
                        return

                    query = parse_qs(parsed.query)
                    for key, value in expected_keys.items():
                        values = query.get(key, [])
                        if not values or str(values[0]) != value:
                            return

                    payload = response.json()
                    if isinstance(payload, dict):
                        captured_payloads.append(payload)
                except Exception:
                    return

            page_obj.on("response", on_response)
            page_obj.goto(f"https://shopee.tw/search?keyword={quote(keyword)}", wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT_MS)
            page_obj.wait_for_timeout(6000)
            current_url = page_obj.url

            context.close()
            if browser is not None:
                browser.close()
    except Exception:
        return [], ["蝦皮瀏覽器備援執行失敗。"]

    if "shopee.tw/verify/" in current_url:
        return [], ["蝦皮觸發流量驗證頁，瀏覽器備援仍被限制。"]

    if not captured_payloads:
        return [], ["蝦皮瀏覽器備援未擷取到商品資料。"]

    normalized: List[Dict[str, Any]] = []
    for payload in captured_payloads:
        error_code = payload.get("error") if isinstance(payload, dict) else None
        if error_code not in (None, 0):
            continue

        items = payload.get("items")
        if not isinstance(items, list):
            data = payload.get("data")
            if isinstance(data, dict):
                items = data.get("items")

        if not isinstance(items, list):
            continue

        for item in items:
            if len(normalized) >= fetch_limit:
                break
            if isinstance(item, dict):
                product = _normalize_shopee_item(item)
                if product is not None:
                    normalized.append(product)

    if not normalized:
        return [], ["蝦皮瀏覽器備援仍未取得可用商品。"]

    return normalized[:fetch_limit], ["蝦皮已使用瀏覽器備援模式。"]


def _fetch_taobao_products_with_browser(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return [], ["淘寶瀏覽器備援無法啟用（缺少 Playwright）。"]

    captured_payloads: List[Dict[str, Any]] = []
    trigger_login = False

    try:
        with sync_playwright() as playwright:
            browser, context = _open_playwright_context(playwright)
            page_obj = context.new_page()

            def on_response(response):
                nonlocal trigger_login
                try:
                    if "mtop.relationrecommend.wirelessrecommend.recommend/2.0" not in response.url:
                        return

                    query = parse_qs(urlparse(response.url).query)
                    raw_data = unquote(query.get("data", [""])[0])
                    if "\"appId\":\"34385\"" not in raw_data:
                        return

                    text = response.text()
                    payload = _parse_jsonp_payload(text)
                    if isinstance(payload, dict):
                        ret_values = payload.get("ret")
                        if isinstance(ret_values, list) and any("LOGIN" in str(item) for item in ret_values):
                            trigger_login = True
                        data_section = payload.get("data")
                        if isinstance(data_section, dict) and "login.taobao.com" in str(data_section.get("url", "")):
                            trigger_login = True
                        captured_payloads.append(payload)
                except Exception:
                    return

            page_obj.on("response", on_response)
            page_obj.goto(f"https://s.taobao.com/search?q={quote(keyword)}", wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT_MS)
            page_obj.wait_for_timeout(9000)
            context.close()
            if browser is not None:
                browser.close()
    except Exception:
        return [], ["淘寶瀏覽器備援執行失敗。"]

    if trigger_login:
            return [], ["淘寶瀏覽器備援需要登入狀態，未登入時無法取得商品。"]

    extracted: List[Dict[str, Any]] = []
    for payload in captured_payloads:
        _extract_taobao_items_from_node(payload, extracted)
        if len(extracted) >= fetch_limit:
            break

    deduplicated: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()
    for item in extracted:
        item_id = str(item.get("id") or "").strip()
        if not item_id or item_id in seen_ids:
            continue
        seen_ids.add(item_id)
        deduplicated.append(item)
        if len(deduplicated) >= fetch_limit:
            break

    paged = _paginate_items(deduplicated, page, fetch_limit)
    if not paged:
        return [], ["淘寶瀏覽器備援未擷取到商品資料。"]

    return paged, ["淘寶已使用瀏覽器備援模式。"]


def _fetch_pchome_products(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    params = {"q": keyword, "page": page, "sort": "rnk/dc"}
    headers = dict(DEFAULT_HEADERS)

    try:
        response = requests.get(PCHOME_SEARCH_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return [], ["PChome 連線失敗。"]
    except ValueError:
        return [], ["PChome 回傳資料格式錯誤。"]

    raw_products = payload.get("prods", [])
    if not isinstance(raw_products, list):
        return [], ["PChome 回傳資料欄位異常。"]

    normalized: List[Dict[str, Any]] = []
    for item in raw_products:
        if isinstance(item, dict):
            product = _normalize_pchome_item(item)
            if product is not None:
                normalized.append(product)

    return normalized[:fetch_limit], []


def _fetch_ruten_products(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    offset = (page - 1) * fetch_limit + 1
    search_params = {
        "q": keyword,
        "type": "direct",
        "sort": "rnk/dc",
        "limit": fetch_limit,
        "offset": offset,
    }
    headers = dict(DEFAULT_HEADERS)

    try:
        search_response = requests.get(
            RUTEN_SEARCH_URL,
            params=search_params,
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        search_response.raise_for_status()
        search_payload = search_response.json()
    except requests.RequestException:
        return [], ["露天搜尋連線失敗。"]
    except ValueError:
        return [], ["露天搜尋回傳資料格式錯誤。"]

    rows = search_payload.get("Rows", [])
    if not isinstance(rows, list) or not rows:
        return [], []

    product_ids: List[str] = []
    for row in rows:
        if isinstance(row, dict):
            product_id = str(row.get("Id") or "").strip()
            if product_id:
                product_ids.append(product_id)

    if not product_ids:
        return [], []

    try:
        detail_response = requests.get(
            RUTEN_PRODUCT_URL,
            params={"id": ",".join(product_ids)},
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        detail_response.raise_for_status()
        detail_payload = detail_response.json()
    except requests.RequestException:
        return [], ["露天商品細節連線失敗。"]
    except ValueError:
        return [], ["露天商品細節回傳資料格式錯誤。"]

    if isinstance(detail_payload, dict):
        detail_items = detail_payload.get("value", [])
    elif isinstance(detail_payload, list):
        detail_items = detail_payload
    else:
        return [], ["露天商品細節回傳欄位異常。"]

    if not isinstance(detail_items, list):
        return [], ["露天商品細節回傳欄位異常。"]

    normalized: List[Dict[str, Any]] = []
    for item in detail_items:
        if isinstance(item, dict):
            product = _normalize_ruten_item(item)
            if product is not None:
                normalized.append(product)

    return normalized[:fetch_limit], []


def _fetch_momo_products(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    url = MOMO_SEARCH_URL_TEMPLATE.format(keyword=quote(keyword))
    headers = dict(DEFAULT_HEADERS)

    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        text = response.text
    except requests.RequestException:
        return [], ["momo 連線失敗。"]

    pattern = re.compile(
        r'\\?"goodsCode\\?":\\?"(?P<id>\d+)\\?"'
        r'[\s\S]*?\\?"goodsName\\?":\\?"(?P<title>.*?)\\?"'
        r'[\s\S]*?\\?"imgUrl\\?":\\?"(?P<image>https?:[^\"]+)\\?"'
        r'[\s\S]*?\\?"goodsUrl\\?":\\?"(?P<url>https?:[^\"]+)\\?"'
        r'[\s\S]*?\\?"SALE_PRICE\\?":\\?"(?P<price>\d+)\\?"'
    )

    normalized: List[Dict[str, Any]] = []
    seen_ids: Set[str] = set()

    for matched in pattern.finditer(text):
        raw = {
            "goodsCode": matched.group("id"),
            "goodsName": matched.group("title"),
            "imgUrl": matched.group("image"),
            "goodsUrl": matched.group("url"),
            "SALE_PRICE": matched.group("price"),
        }

        if raw["goodsCode"] in seen_ids:
            continue

        product = _normalize_momo_item(raw)
        if product is not None:
            normalized.append(product)
            seen_ids.add(raw["goodsCode"])

    if not normalized:
        return [], ["momo 暫時無法解析商品列表。"]

    return _paginate_items(normalized, page, fetch_limit), []


def _fetch_yahoo_products(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    headers = dict(DEFAULT_HEADERS)

    try:
        response = requests.get(
            YAHOO_SEARCH_URL,
            params={"p": keyword},
            headers=headers,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        text = response.text
    except requests.RequestException:
        return [], ["Yahoo購物中心連線失敗。"]

    matched = re.search(r'<script id="isoredux-data"[^>]*>([\s\S]*?)</script>', text)
    if not matched:
        return [], ["Yahoo購物中心頁面資料解析失敗。"]

    try:
        payload = json.loads(matched.group(1))
    except json.JSONDecodeError:
        return [], ["Yahoo購物中心資料格式錯誤。"]

    raw_hits = payload.get("search", {}).get("ecsearch", {}).get("hits", [])
    if not isinstance(raw_hits, list):
        return [], ["Yahoo購物中心回傳欄位異常。"]

    normalized: List[Dict[str, Any]] = []
    for item in raw_hits:
        if isinstance(item, dict):
            product = _normalize_yahoo_item(item)
            if product is not None:
                normalized.append(product)

    return _paginate_items(normalized, page, fetch_limit), []


def _fetch_shopee_products(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    newest = (page - 1) * fetch_limit
    params = {
        "by": "relevancy",
        "keyword": keyword,
        "limit": fetch_limit,
        "newest": newest,
        "order": "desc",
        "page_type": "search",
        "scenario": "PAGE_GLOBAL_SEARCH",
        "version": 2,
    }
    headers = {
        **DEFAULT_HEADERS,
        "x-api-source": "pc",
        "referer": f"https://shopee.tw/search?keyword={quote(keyword)}",
    }

    try:
        response = requests.get(SHOPEE_SEARCH_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.RequestException:
        return [], ["蝦皮搜尋連線失敗。"]

    try:
        payload = response.json()
    except ValueError:
        return [], ["蝦皮搜尋回傳資料格式錯誤。"]

    if response.status_code in (401, 403, 429):
        error_code = payload.get("error") if isinstance(payload, dict) else None
        blocked_warning = ""
        if error_code not in (None, 0):
            blocked_warning = f"蝦皮目前限制搜尋介面（代碼 {error_code}），暫時無法穩定擷取商品資料。"
        else:
            blocked_warning = f"蝦皮目前限制搜尋介面（HTTP {response.status_code}），暫時無法穩定擷取商品資料。"

        if ENABLE_BROWSER_FALLBACK:
            browser_products, browser_warnings = _fetch_shopee_products_with_browser(keyword, page, fetch_limit)
            if browser_products:
                return browser_products, browser_warnings
            return [], [blocked_warning, *browser_warnings]

        return [], [blocked_warning]

    if response.status_code >= 500:
        return [], [f"蝦皮服務暫時異常（HTTP {response.status_code}）。"]

    if response.status_code >= 400:
        return [], [f"蝦皮搜尋請求失敗（HTTP {response.status_code}）。"]

    error_code = payload.get("error") if isinstance(payload, dict) else None
    if error_code not in (None, 0):
        if ENABLE_BROWSER_FALLBACK:
            browser_products, browser_warnings = _fetch_shopee_products_with_browser(keyword, page, fetch_limit)
            if browser_products:
                return browser_products, browser_warnings
            return [], [f"蝦皮目前限制搜尋介面（代碼 {error_code}），暫時無法穩定擷取商品資料。", *browser_warnings]
        return [], [f"蝦皮目前限制搜尋介面（代碼 {error_code}），暫時無法穩定擷取商品資料。"]

    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict):
            items = data.get("items")

    if not isinstance(items, list):
        if ENABLE_BROWSER_FALLBACK:
            browser_products, browser_warnings = _fetch_shopee_products_with_browser(keyword, page, fetch_limit)
            if browser_products:
                return browser_products, browser_warnings
            return [], ["蝦皮目前未回傳可用商品列表。", *browser_warnings]
        return [], ["蝦皮目前未回傳可用商品列表。"]

    normalized: List[Dict[str, Any]] = []
    for item in items:
        if len(normalized) >= fetch_limit:
            break
        if isinstance(item, dict):
            product = _normalize_shopee_item(item)
            if product is not None:
                normalized.append(product)

    if not normalized:
        if ENABLE_BROWSER_FALLBACK:
            browser_products, browser_warnings = _fetch_shopee_products_with_browser(keyword, page, fetch_limit)
            if browser_products:
                return browser_products, browser_warnings
            return [], ["蝦皮目前未回傳可用商品列表。", *browser_warnings]
        return [], ["蝦皮目前未回傳可用商品列表。"]

    return normalized, []


def _fetch_taobao_products(keyword: str, page: int, fetch_limit: int) -> Tuple[List[Dict[str, Any]], List[str]]:
    headers = dict(DEFAULT_HEADERS)

    try:
        response = requests.get(TAOBAO_SEARCH_URL, params={"q": keyword}, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        text = response.text
    except requests.RequestException:
        if ENABLE_BROWSER_FALLBACK:
            browser_products, browser_warnings = _fetch_taobao_products_with_browser(keyword, page, fetch_limit)
            if browser_products:
                return browser_products, browser_warnings
            return [], ["淘寶搜尋連線失敗。", *browser_warnings]
        return [], ["淘寶搜尋連線失敗。"]

    # Taobao often returns a skeleton page or verification flow without item payload.
    item_pattern = re.compile(
        r'"nid":"(?P<id>\d+)"[\s\S]*?"raw_title":"(?P<title>.*?)"[\s\S]*?"view_price":"(?P<price>[0-9.]+)"'
    )

    normalized: List[Dict[str, Any]] = []
    for matched in item_pattern.finditer(text):
        item_id = matched.group("id")
        title = _decode_escaped(matched.group("title"))
        price_text = matched.group("price")
        price = _safe_price(price_text)

        if not item_id or not title:
            continue

        availability, availability_confidence, availability_signals = _resolve_availability(
            text_sources=[title],
            default_if_unknown="unknown",
        )
        normalized.append(
            _normalize_common_item(
                product_id=item_id,
                source="淘寶",
                title=title,
                price=price,
                original_price=None,
                image_url="",
                product_url=f"https://item.taobao.com/item.htm?id={item_id}",
                availability=availability,
                availability_confidence=availability_confidence,
                availability_signals=availability_signals,
            )
        )

    if not normalized:
        if ENABLE_BROWSER_FALLBACK:
            browser_products, browser_warnings = _fetch_taobao_products_with_browser(keyword, page, fetch_limit)
            if browser_products:
                return browser_products, browser_warnings
            return [], ["淘寶目前僅回傳骨架頁或驗證頁，暫時無法穩定擷取商品資料。", *browser_warnings]
        return [], ["淘寶目前僅回傳骨架頁或驗證頁，暫時無法穩定擷取商品資料。"]

    return _paginate_items(normalized, page, fetch_limit), []


def _sort_products(products: List[Dict[str, Any]], sort_key: str) -> List[Dict[str, Any]]:
    if sort_key == "price_asc":
        return sorted(products, key=lambda item: (item["price"] is None, item["price"] or 0))
    if sort_key == "price_desc":
        return sorted(products, key=lambda item: (item["price"] is None, -(item["price"] or 0)))
    return products


def _summarize_availability(products: List[Dict[str, Any]]) -> Dict[str, int]:
    summary = {"in_stock": 0, "out_of_stock": 0, "unknown": 0}
    for item in products:
        status = str(item.get("availability") or "unknown")
        if status not in summary:
            status = "unknown"
        summary[status] += 1
    return summary


def _merge_provider_results(
    keyword: str,
    page: int,
    fetch_limit: int,
    providers: List[str],
) -> Tuple[List[Dict[str, Any]], List[str], Dict[str, int], Dict[str, Dict[str, int]]]:
    all_products: List[Dict[str, Any]] = []
    warnings: List[str] = []
    provider_counts: Dict[str, int] = {}
    provider_availability_counts: Dict[str, Dict[str, int]] = {}

    for provider in providers:
        if provider == "pchome":
            products, provider_warnings = _fetch_pchome_products(keyword, page, fetch_limit)
        elif provider == "ruten":
            products, provider_warnings = _fetch_ruten_products(keyword, page, fetch_limit)
        elif provider == "momo":
            products, provider_warnings = _fetch_momo_products(keyword, page, fetch_limit)
        elif provider == "yahoo":
            products, provider_warnings = _fetch_yahoo_products(keyword, page, fetch_limit)
        elif provider == "shopee":
            products, provider_warnings = _fetch_shopee_products(keyword, page, fetch_limit)
        elif provider == "taobao":
            products, provider_warnings = _fetch_taobao_products(keyword, page, fetch_limit)
        else:
            products, provider_warnings = [], [f"不支援的來源：{provider}"]

        provider_counts[provider] = len(products)
        provider_availability_counts[provider] = {
            "total": len(products),
            **_summarize_availability(products),
        }
        all_products.extend(products)
        warnings.extend(provider_warnings)

    deduplicated: List[Dict[str, Any]] = []
    seen_keys: Set[Tuple[str, str]] = set()

    for item in all_products:
        key = (str(item.get("source", "")), str(item.get("id", "")))
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduplicated.append(item)

    return deduplicated, warnings, provider_counts, provider_availability_counts


@require_GET
def get_data(request):
    keyword = request.GET.get("keyword", "").strip()
    if not keyword:
        return JsonResponse({"error": "請輸入商品關鍵字。"}, status=400)

    page = _safe_int(request.GET.get("page"), default=1, min_value=1, max_value=20)
    limit = _safe_int(request.GET.get("limit"), default=DEFAULT_LIMIT, min_value=1, max_value=MAX_LIMIT)

    raw_sort = str(request.GET.get("sort", "relevance")).strip().lower()
    sort = raw_sort if raw_sort in SORT_OPTIONS else "relevance"

    providers = _parse_providers(str(request.GET.get("providers", "all")))

    fetch_limit = max(limit, DEFAULT_LIMIT)
    products, warnings, provider_counts, provider_availability_counts = _merge_provider_results(
        keyword=keyword,
        page=page,
        fetch_limit=fetch_limit,
        providers=providers,
    )

    products = _sort_products(products, sort)[:limit]
    availability_summary = _summarize_availability(products)

    return JsonResponse(
        {
            "keyword": keyword,
            "count": len(products),
            "page": page,
            "limit": limit,
            "sort": sort,
            "providers": providers,
            "provider_counts": provider_counts,
            "provider_availability_counts": provider_availability_counts,
            "availability_summary": availability_summary,
            "results": products,
            "warnings": warnings,
        },
        json_dumps_params={"ensure_ascii": False},
    )



