import "bootstrap/dist/css/bootstrap.min.css";
import "../css/Footer.css";
import { Container, Row, Col } from "react-bootstrap";
import { FaHome, FaEnvelope, FaPhone } from "react-icons/fa";

function Footer() {
  return (
    <footer className="text-center">
      <section className="d-flex justify-content-center border-bottom">
        <Container className="text-center text-md-start mt-5">
          <Row className="mt-3">
            <Col md={3} xl={2} className="mx-auto mb-4">
              <p>
                <a href="/常見問題" className="text-reset">
                  常見問題
                </a>
              </p>
              <p>
                <a href="/意見反映" className="text-reset">
                  意見反映
                </a>
              </p>
            </Col>

            <Col md={3} xl={2} className="mx-auto mb-4">
              <p>
                <a href="/關於我們" className="text-reset">
                  關於我們
                </a>
              </p>
              <p>
                <a href="/服務條款" className="text-reset">
                  服務條款
                </a>
              </p>
              <p>
                <a href="/隱私權政策" className="text-reset">
                  隱私權政策
                </a>
              </p>
            </Col>

            <Col md={6} xl={4} className="mx-auto mb-4">
              <h6 className="text-uppercase fw-bold mb-4">聯絡我們</h6>
              <p>
                <FaHome className="me-3" />
                Zhudong, Hsinchu 310, TW
              </p>
              <p>
                <FaEnvelope className="me-3" />
                chihuahuafanclub@gmail.com
              </p>
              <p>
                <FaPhone className="me-3" />
                +886 988279013
              </p>
            </Col>
          </Row>
        </Container>
      </section>
    </footer>
  );
}

export default Footer;