import React, { useState } from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import Button from 'react-bootstrap/Button';
import Container from 'react-bootstrap/Container';
import Form from 'react-bootstrap/Form';
import Navbar from 'react-bootstrap/Navbar';

function Header() {
    const [data, setData] = useState([]);
    const [keyword, setKeyword] = useState('');
    const [, setLoading] = useState(false);

    const fetchData = async () => {
        try {
            const response = await fetch(`http://localhost:8000/api/search/?keyword=${keyword}`);
            const jsonData = await response.json();
            setData(jsonData);
            setLoading(false);
        } catch (error) {
            console.error(error);
            setLoading(false);
        }
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        setLoading(true);
        fetchData().then(() => {
            setLoading(false);
        });
    };

    return (
        <div>
            <Navbar bg="dark" data-bs-theme="dark">
                <Container>
                    <Navbar.Brand>比價網站</Navbar.Brand>
                    <Container>
                        <Form className="d-flex form-control-lg" onSubmit={handleSubmit}>
                            <Form.Control
                                type="search"
                                placeholder="物品名稱"
                                className="me-2"
                                aria-label="Search"
                                onChange={(event) => setKeyword(event.target.value)}
                                value={keyword}
                            />
                            <Button type="submit" variant="outline-success" className="text-nowrap">
                                搜尋
                            </Button>
                        </Form>
                    </Container>
                </Container>
            </Navbar>
            <ul>
                {data.length > 0 ? (
                    <p>${data}</p>
                ) : (
                    <p></p>
                )}
            </ul>
        </div>
    );
}

export default Header;