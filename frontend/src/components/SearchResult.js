import '../css/SearchResult.css';
import { useLocation } from 'react-router-dom';
import Search from "./Search";
import Container from 'react-bootstrap/Container';
import Statement from './Statement';

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
                <p className='searchresult-count'>「{keyword}」 商品搜尋結果共 " {count} " 筆資料</p>
                <ol>
                    {dataparse.filter(item => !item.count).map(item => (
                        <li>
                            <div className='row'>
                                <div className='col col-lg-2'>
                                    <img src={`https://cs-a.ecimg.tw/${item.pics}`} />
                                </div>
                                <div className='col'>
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
            </Container>
            <Statement />
        </div>
    );
}

export default SearchResult;
