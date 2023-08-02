import "bootstrap/dist/css/bootstrap.min.css";
import "./css/index.css";
import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Search from "../../components/Search";
import Container from "react-bootstrap/Container";
import Statement from "../../components/Statement";

function SearchResult() {
    const location = useLocation();
    const navigate = useNavigate();
    const keyword = new URLSearchParams(location.search).get("q");
    const [data, setData] = useState();
    const [count, setCount] = useState(0);
    const [sortOption, setSortOption] = useState("");
    const [sortedData, setSortedData] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch(`http://123.241.65.154:8000/api/search/?keyword=${keyword}`);
                const data = await response.json();
                const dataparse = JSON.parse(data);
                const count = dataparse[dataparse.length - 1].count;
                setData(dataparse);
                setCount(count);
            } catch (error) {
                console.error(error);
            }
        };
        fetchData();
    }, [keyword]);

    useEffect(() => {
        if (data) {
            let sorted = data.filter(item => !item.count && item.name);
            if (sortOption === "asc") {
                sorted = sorted.sort((a, b) => a.price - b.price);
            }
            if (sortOption === "desc") {
                sorted = sorted.sort((a, b) => b.price - a.price);
            }
            setSortedData(sorted);
        }
    }, [sortOption, data]);

    const handleSortOptionChange = (option) => {
        if (option !== sortOption) {
            setSortOption(option);
            const searchParams = new URLSearchParams(location.search);
            searchParams.set("sort", option);
            navigate({ search: searchParams.toString() });
        }
    };
    
    return (
        <Container>
            <Search />
            <Container>
                {data && Array.isArray(data) ? ( // Conditional rendering based on data availability
                    <>
                        <p className="searchresult-count">「{keyword}」 商品搜尋結果共 "{count}" 筆資料</p>
                        <div className="searchresult-sort">
                            <a
                                className={sortOption === "" ? "active-link" : "inactive-link"}
                                onClick={() => handleSortOptionChange("")}
                            >
                                {"綜合排序"}
                            </a>
                            <a
                                className={sortOption === "asc" ? "active-link" : "inactive-link"}
                                onClick={() => handleSortOptionChange("asc")}
                            >
                                {"價格低 -> 高"}
                            </a>
                            <a
                                className={sortOption === "desc" ? "active-link" : "inactive-link"}
                                onClick={() => handleSortOptionChange("desc")}
                            >
                                {"價格高 -> 低"}
                            </a>
                        </div>
                        <ol>
                            {(!sortedData ? data : sortedData).map(item => (
                                <li key={item.id}>
                                    <div className="row">
                                        <div className="col col-lg-2">
                                            <img src={`https://cs-a.ecimg.tw/${item.pics}`} alt={item.name} />
                                        </div>
                                        <div className="col">
                                            <div>
                                                <a>
                                                    {item.name}
                                                </a>
                                            </div>
                                            <div>
                                                <p>${item.price}</p>
                                            </div>
                                        </div>
                                    </div>
                                </li>
                            ))}
                        </ol>
                    </>
                ) : (
                    <p>Loading...</p> // Placeholder for when data is being fetched
                )}
            </Container>
            <Statement />
        </Container>
    );
}

export default SearchResult;
