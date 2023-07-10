import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../css/Search.css';
import Container from 'react-bootstrap/Container';
import Form from 'react-bootstrap/Form';
import Button from 'react-bootstrap/Button';

function Search() {
    const [keyword, setKeyword] = useState('');
    const navigate = useNavigate();

    const fetchData = async () => {
        try {
            const response = await fetch(`http://localhost:8000/api/search/?keyword=${keyword}`);
            const data = await response.json();
            navigate(`/s/?q=${keyword}`, { state: { keyword: keyword, data: data } });
        } catch (error) {
            console.error(error);
        }
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        fetchData();
    };

    return (
        <div>
            <Container fluid='auto' className='home-container-md'>
                <Container>
                    <Form className="d-flex form-control-lg form" onSubmit={handleSubmit}>
                        <Form.Control
                            type="search"
                            placeholder="請輸入搜索關鍵字，例如：RTX-4090"
                            className="me-2 form-control"
                            aria-label="Search"
                            onChange={(event) => setKeyword(event.target.value)}
                        />
                        <Button type="submit" variant="outline-success" className="text-nowrap">
                            搜索
                        </Button>
                    </Form>
                </Container>
            </Container>
        </div>
    );
}

export default Search;