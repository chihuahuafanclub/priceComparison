import 'bootstrap/dist/css/bootstrap.min.css';
import '../css/Header.css';

import Container from 'react-bootstrap/Container';
import Navbar from 'react-bootstrap/Navbar';
import Nav from 'react-bootstrap/Nav';

function Header() {
    return (
        <div>
            <Navbar bg="dark" data-bs-theme="dark">
                <Container>
                    <Navbar.Brand className='navbar-brand'>比奇寶</Navbar.Brand>
                    <Nav className="me-auto navbar-link">
                        <Nav.Link href="/">首頁精選</Nav.Link>
                        <Nav.Link href="/瀏覽分類">瀏覽分類</Nav.Link>
                    </Nav>
                </Container>
            </Navbar>
        </div>
    );
}

export default Header;