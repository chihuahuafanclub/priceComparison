import React, { useState } from "react";
import "./Home.css";

const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || (window.location.hostname === "localhost" ? "http://localhost:8000" : "");
const DEFAULT_LIMIT = 60;
const MAX_PAGE = 20;

const SORT_OPTIONS = [
  { value: "relevance", label: "相關度" },
  { value: "price_asc", label: "價格低到高" },
  { value: "price_desc", label: "價格高到低" },
];

const PROVIDER_OPTIONS = [
  { value: "pchome", label: "PChome 24h", restricted: false },
  { value: "ruten", label: "露天拍賣", restricted: false },
  { value: "momo", label: "momo購物網", restricted: false },
  { value: "yahoo", label: "Yahoo購物中心", restricted: false },
  { value: "shopee", label: "蝦皮購物（可能受限）", restricted: true },
  { value: "taobao", label: "淘寶（可能受限）", restricted: true },
];

function formatCurrency(value) {
  if (typeof value !== "number") {
    return "價格未提供";
  }

  return new Intl.NumberFormat("zh-TW", {
    style: "currency",
    currency: "TWD",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatInteger(value) {
  if (typeof value !== "number") {
    return "";
  }
  return new Intl.NumberFormat("zh-TW", { maximumFractionDigits: 0 }).format(value);
}

function formatRating(value) {
  if (typeof value !== "number") {
    return "";
  }
  return value.toFixed(1);
}

async function fetchProducts({ keyword, sort, limit, providers, page }) {
  const params = new URLSearchParams({
    keyword,
    sort,
    limit: String(limit),
    providers: providers.join(","),
    page: String(page),
  });

  const response = await fetch(`${API_BASE_URL}/api/search/?${params.toString()}`);
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload.error || "搜尋失敗，請稍後再試。");
  }

  return payload;
}

function ProductCard({ product, index }) {
  const [imageError, setImageError] = useState(false);
  const hasImage = Boolean(product.image_url) && !imageError;
  const discountText =
    typeof product.discount_amount === "number" && product.discount_amount > 0
      ? `省 ${formatCurrency(product.discount_amount)}`
      : "";
  const ratingText =
    typeof product.rating === "number"
      ? `${formatRating(product.rating)}${typeof product.review_count === "number" ? `（${formatInteger(product.review_count)} 評）` : ""}`
      : "";
  const stockText = typeof product.stock_qty === "number" ? String(product.stock_qty) : "";
  const tags = Array.isArray(product.tags) ? product.tags.filter((tag) => String(tag).trim()).slice(0, 6) : [];

  return (
    <a
      className="product-card"
      href={product.product_url}
      target="_blank"
      rel="noreferrer"
      style={{ animationDelay: `${Math.min(index * 40, 360)}ms` }}
    >
      <div className="product-image-wrap">
        {hasImage ? (
          <img
            className="product-image"
            src={product.image_url}
            alt={product.title}
            loading="lazy"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="product-image-placeholder">無商品圖片</div>
        )}
      </div>

      <div className="product-content">
        <span className="product-source">{product.source}</span>
        <h2 className="product-title">{product.title}</h2>

        <div className="price-row">
          <span className="price-current">{formatCurrency(product.price)}</span>
          {typeof product.original_price === "number" && product.original_price > (product.price || 0) ? (
            <span className="price-original">{formatCurrency(product.original_price)}</span>
          ) : null}
          {discountText ? <span className="price-discount">{discountText}</span> : null}
        </div>

        <dl className="meta-list">
          {product.shop_name ? (
            <>
              <dt>店家</dt>
              <dd>{product.shop_name}</dd>
            </>
          ) : null}
          {stockText ? (
            <>
              <dt>庫存</dt>
              <dd>{stockText}</dd>
            </>
          ) : null}
          {typeof product.sales_count === "number" ? (
            <>
              <dt>銷量</dt>
              <dd>{formatInteger(product.sales_count)}</dd>
            </>
          ) : null}
          {ratingText ? (
            <>
              <dt>評分</dt>
              <dd>{ratingText}</dd>
            </>
          ) : null}
          {product.shipping_text ? (
            <>
              <dt>運送</dt>
              <dd>{product.shipping_text}</dd>
            </>
          ) : null}
          {product.location ? (
            <>
              <dt>地區</dt>
              <dd>{product.location}</dd>
            </>
          ) : null}
        </dl>

        {tags.length > 0 ? (
          <div className="tag-list">
            {tags.map((tag) => (
              <span key={`${product.id}-${tag}`} className="tag-pill">
                {tag}
              </span>
            ))}
          </div>
        ) : null}

        <span className="product-link">查看商品頁</span>
      </div>
    </a>
  );
}

export default function Home() {
  const [queryInput, setQueryInput] = useState("");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [sort, setSort] = useState("relevance");
  const [limit, setLimit] = useState(DEFAULT_LIMIT);
  const [page, setPage] = useState(1);
  const [providers, setProviders] = useState(PROVIDER_OPTIONS.filter((item) => !item.restricted).map((item) => item.value));
  const [results, setResults] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runSearch = async ({ keyword, nextSort, nextLimit, nextProviders, nextPage }) => {
    const cleanKeyword = keyword.trim();
    if (!cleanKeyword) {
      setError("請輸入商品關鍵字。");
      setResults([]);
      setWarnings([]);
      return;
    }

    if (nextProviders.length === 0) {
      setError("請至少選擇一個來源。");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const data = await fetchProducts({
        keyword: cleanKeyword,
        sort: nextSort,
        limit: nextLimit,
        providers: nextProviders,
        page: nextPage,
      });

      setResults(Array.isArray(data.results) ? data.results : []);
      setWarnings(Array.isArray(data.warnings) ? data.warnings : []);
      setSearchKeyword(cleanKeyword);
      setPage(nextPage);
    } catch (requestError) {
      setResults([]);
      setWarnings([]);
      setError(requestError.message || "搜尋失敗，請稍後再試。");
    } finally {
      setLoading(false);
    }
  };

  const runWithCurrentQuery = async (nextPage, nextSort = sort, nextLimit = limit, nextProviders = providers) => {
    const keyword = searchKeyword || queryInput;
    await runSearch({
      keyword,
      nextSort,
      nextLimit,
      nextProviders,
      nextPage,
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    await runSearch({
      keyword: queryInput,
      nextSort: sort,
      nextLimit: limit,
      nextProviders: providers,
      nextPage: 1,
    });
  };

  const handleSortChange = async (event) => {
    const nextSort = event.target.value;
    setSort(nextSort);

    if (searchKeyword) {
      await runWithCurrentQuery(1, nextSort, limit, providers);
    }
  };

  const handleLimitChange = async (event) => {
    const nextLimit = Number(event.target.value);
    setLimit(nextLimit);

    if (searchKeyword) {
      await runWithCurrentQuery(1, sort, nextLimit, providers);
    }
  };

  const handleProviderToggle = async (provider) => {
    const exists = providers.includes(provider);
    const nextProviders = exists ? providers.filter((item) => item !== provider) : [...providers, provider];
    setProviders(nextProviders);

    if (searchKeyword && nextProviders.length > 0) {
      await runWithCurrentQuery(1, sort, limit, nextProviders);
    }
  };

  const handlePageChange = async (nextPage) => {
    if (!searchKeyword || nextPage < 1 || nextPage > MAX_PAGE || loading) {
      return;
    }

    await runWithCurrentQuery(nextPage, sort, limit, providers);
  };

  const canGoPrev = page > 1 && !loading && Boolean(searchKeyword);
  const canGoNext = results.length >= limit && page < MAX_PAGE && !loading && Boolean(searchKeyword);

  return (
    <main className="page">
      <section className="hero">
        <p className="hero-kicker">PriceComparison</p>
        <h1 className="hero-title">商品比價</h1>
        <p className="hero-subtitle">集中顯示各平台價格與商品資訊，快速找到合適選擇。</p>

        <form className="search-form" onSubmit={handleSubmit}>
          <label className="sr-only" htmlFor="keyword-input">
            商品關鍵字
          </label>
          <input
            id="keyword-input"
            className="search-input"
            placeholder="例如：iPhone 15 Pro、Switch 2、Dyson V12、PS5、AirPods Pro 2"
            value={queryInput}
            onChange={(event) => setQueryInput(event.target.value)}
          />
          <button className="search-button" type="submit" disabled={loading}>
            {loading ? "搜尋中..." : "開始搜尋"}
          </button>
        </form>

        <div className="toolbar">
          <label className="toolbar-item" htmlFor="sort-select">
            排序
            <select id="sort-select" value={sort} onChange={handleSortChange}>
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>

          <label className="toolbar-item" htmlFor="limit-select">
            每頁筆數
            <select id="limit-select" value={limit} onChange={handleLimitChange}>
              <option value={24}>24</option>
              <option value={36}>36</option>
              <option value={60}>60</option>
              <option value={96}>96</option>
              <option value={120}>120</option>
            </select>
          </label>

          <label className="toolbar-item" htmlFor="page-select">
            頁碼
            <select id="page-select" value={page} onChange={(event) => handlePageChange(Number(event.target.value))}>
              {Array.from({ length: MAX_PAGE }, (_, i) => i + 1).map((p) => (
                <option key={p} value={p}>
                  第 {p} 頁
                </option>
              ))}
            </select>
          </label>

          <div className="pager-inline">
            <button className="pager-button" type="button" disabled={!canGoPrev} onClick={() => handlePageChange(page - 1)}>
              上一頁
            </button>
            <button className="pager-button" type="button" disabled={!canGoNext} onClick={() => handlePageChange(page + 1)}>
              下一頁
            </button>
          </div>

          <div className="provider-group" role="group" aria-label="資料來源">
            {PROVIDER_OPTIONS.map((option) => {
              const checked = providers.includes(option.value);
              return (
                <label key={option.value} className="provider-check">
                  <input type="checkbox" checked={checked} onChange={() => handleProviderToggle(option.value)} />
                  {option.label}
                </label>
              );
            })}
          </div>
          <div className="provider-note">蝦皮、淘寶可能因反爬限制導致資料較少，建議以 PChome/露天/momo/Yahoo 為主。</div>

          <div className="result-meta" aria-live="polite">
            {searchKeyword ? `關鍵字「${searchKeyword}」第 ${page} 頁，共 ${results.length} 筆` : "輸入關鍵字後開始搜尋"}
          </div>
        </div>
      </section>

      {error ? <div className="status status-error">{error}</div> : null}
      {!error && warnings.length > 0 ? <div className="status status-warning">{warnings.join(" ")}</div> : null}
      {loading ? <div className="status">正在抓取商品資料...</div> : null}

      {!loading && !error && searchKeyword && results.length === 0 ? (
        <div className="status">找不到符合條件的商品，請調整關鍵字。</div>
      ) : null}

      <section className="results-grid">
        {results.map((product, index) => (
          <ProductCard key={`${product.source}-${product.id}-${index}`} product={product} index={index} />
        ))}
      </section>
    </main>
  );
}
