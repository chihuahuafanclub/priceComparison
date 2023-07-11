import '../css/Footer.css';
import { MDBFooter, MDBContainer, MDBRow, MDBCol, MDBIcon } from 'mdb-react-ui-kit';

function Footer() {
    return (
        <MDBFooter color='white' bgColor='dark' className='text-center'>
            <section className='d-flex justify-content-center border-bottom'>
                <MDBContainer className='text-center text-md-start mt-5'>
                    <MDBRow className='mt-3'>
                        <MDBCol md="3" xl="2" className='mx-auto mb-4'>
                            <p>
                                <a href='/常見問題' className='text-reset'>
                                    常見問題
                                </a>
                            </p>
                            <p>
                                <a href='/意見反映' className='text-reset'>
                                    意見反映
                                </a>
                            </p>
                        </MDBCol>

                        <MDBCol md="3" xl="2" className='mx-auto mb-4'>
                            <p>
                                <a href='關於我們' className='text-reset'>
                                    關於我們
                                </a>
                            </p>
                            <p>
                                <a href='/服務條款' className='text-reset'>
                                    服務條款
                                </a>
                            </p>
                            <p>
                                <a href='/隱私權政策' className='text-reset'>
                                    隱私權政策
                                </a>
                            </p>
                        </MDBCol>

                        <MDBCol md="6" xl="4" className='mx-auto mb-4'>
                            <h6 className='text-uppercase fw-bold mb-4'>聯絡我們</h6>
                            <p>
                                <MDBIcon icon="home" className="me-3" />
                                Zhudong, Hsinchu 310, TW
                            </p>
                            <p>
                                <MDBIcon icon="envelope" className="me-3" />
                                chihuahuafanclub@gmail.com
                            </p>
                            <p>
                                <MDBIcon icon="phone" className="me-3" />
                                +886 988279013
                            </p>
                        </MDBCol>
                    </MDBRow>
                </MDBContainer>
            </section>
        </MDBFooter>
    )
}

export default Footer;