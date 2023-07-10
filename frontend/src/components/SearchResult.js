import { useLocation } from 'react-router-dom';
import '../css/SearchResult.css'
import Search from "./Search";
import Container from 'react-bootstrap/Container';

function SearchResult() {
    const location = useLocation();
    const keyword = location.state.keyword;
    const data = location.state.data;
    const dataparse = JSON.parse(data);
    const count = dataparse[dataparse.length - 1].count;

    return (
        <div>
            <Search />
            <Container>
                <p>「{keyword}」 商品搜尋結果共 " {count} " 筆資料</p>
                <ol>
                    {dataparse.filter(item => !item.count).map(item => (
                        <li key={item.name}>
                            <span>
                                <img src={`https://cs-a.ecimg.tw/${item.pics}`} />
                            </span>
                            <span className='items_container'>
                                {item.name}
                            </span>
                        </li>
                    ))}
                </ol>
            </Container>
        </div>
    );
}

export default SearchResult;
