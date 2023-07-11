import '../css/HomeBody.css';
import Container from 'react-bootstrap/Container';

function HomeBody() {
    return (
        <div>
            <Container fluid="auto" className='home-container-auto'>
                <Container fluid='md' className='home-container-md'>
                </Container>
            </Container>
        </div >
    );
}

export default HomeBody;