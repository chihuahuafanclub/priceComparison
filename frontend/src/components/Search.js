import "bootstrap/dist/css/bootstrap.min.css";
import "../css/Search.css";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Button from "react-bootstrap/Button";

function Search() {
    const [keyword, setKeyword] = useState("");
    const navigate = useNavigate();

    const handleSubmit = (event) => {
        event.preventDefault();
        try {
            navigate(`/s/?q=${keyword}`);
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <Container>
            <Form className="d-flex form-control-lg search-form" onSubmit={handleSubmit}>
                <Form.Control
                    type="search"
                    placeholder="請輸入搜尋關鍵字，例如：RTX-4090"
                    className="me-2 search-form-control"
                    aria-label="Search"
                    onChange={(event) => setKeyword(event.target.value)}
                    required
                />
                <Button type="submit" variant="outline-success" className="text-nowrap">
                    搜索
                </Button>
            </Form>
        </Container>
    );
}

export default Search;