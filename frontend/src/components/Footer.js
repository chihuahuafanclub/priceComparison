import React from "react";
import { MDBFooter, MDBContainer, MDBRow, MDBCol, MDBIcon } from 'mdb-react-ui-kit';

function Footer() {
    return (
        <MDBFooter color='white' bgColor='dark' className='text-center'>
            <section className='d-flex justify-content-center border-bottom'>
                <MDBContainer className='text-center text-md-start mt-5'>
                    <MDBRow className='mt-3'>
                        <MDBCol md="3" lg="4" xl="3" className='mx-auto mb-4'>
                            <h6 className='text-uppercase fw-bold mb-4'>
                                <MDBIcon icon="gem" className="me-3" />
                                網站名稱
                            </h6>
                            <p>
                                請把網站介紹寫這裡。
                            </p>
                        </MDBCol>

                        <MDBCol md="2" lg="2" xl="2" className='mx-auto mb-4'>
                            <p>
                                <a href='/about' className='text-reset'>
                                    關於我們
                                </a>
                            </p>
                            <p>
                                <a href='#!' className='text-reset'>
                                    加入我們
                                </a>
                            </p>
                        </MDBCol>

                        <MDBCol md="3" lg="2" xl="2" className='mx-auto mb-4'>
                            <p>
                                <a href='#!' className='text-reset'>
                                    常見問題
                                </a>
                            </p>
                            <p>
                                <a href='#!' className='text-reset'>
                                    意見反映
                                </a>
                            </p>
                            <p>
                                <a href='#!' className='text-reset'>
                                    服務條款
                                </a>
                            </p>
                            <p>
                                <a href='#!' className='text-reset'>
                                    隱私權政策
                                </a>
                            </p>
                        </MDBCol>

                        <MDBCol md="4" lg="3" xl="3" className='mx-auto mb-md-0 mb-4'>
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

            <div className='text-center p-4' style={{ backgroundColor: 'rgba(0, 0, 0, 0.05)' }}>
                © 2023 Chihuahua Fan Club
            </div>
        </MDBFooter>
    )
}

export default Footer;