import "bootstrap/dist/css/bootstrap.min.css";
import "./css/index.css";
import Container from "react-bootstrap/Container";

function Privacy() {
    return (
        <Container fluid="auto" className="privacy-container-auto">
            <Container fluid="md" className="privacy-container-md">
                <article>
                    <h1 className="text-center">隱私權政策</h1>
                    <div className="privacy-article">
                        <p className="text-center mt-3" />
                        感謝您使用我們的網站。我們非常重視您的隱私權並致力於保護您的個人資訊。本隱私權政策將向您解釋我們收集、使用和保護您的個人資訊的方式。請仔細閱讀以下內容。
                        <h2>
                            資訊收集與使用
                        </h2>
                        <p className="text-center mt-3" />
                        當您訪問我們的網站時，我們可能會要求您提供某些個人資訊，以便向您提供更好的服務。這些資訊可能包括但不限於您的姓名、電子郵件地址、聯絡方式等。我們僅會在符合法律規定的情況下收集這些資訊。我們承諾不會出售、共享或租借您的個人資訊給任何第三方，除非獲得您的明確授權或法律另有規定。
                        <h2>
                            資訊使用目的
                        </h2>
                        <p className="text-center mt-3" />
                        我們可能會使用您提供的個人資訊來：
                        提供、維護和改進我們的網站和服務。
                        向您提供相關產品或服務的資訊。
                        回應您的詢問和提供客戶支援。
                        管理您的帳戶和處理您的交易。
                        發送定期電子郵件通訊，包括促銷活動、產品更新等。
                        進行市場調查、統計分析和改善我們的業務運營。
                        <h2>
                            隱私保護
                        </h2>
                        <p className="text-center mt-3" />
                        我們採取合理的安全措施來保護您的個人資訊免於未經授權的存取、使用或洩露。然而，請注意，沒有任何一種傳輸方法或電子存儲方法是100% 安全的。我們無法保證在互聯網上傳輸的資訊的安全性。
                        <h2>
                            Cookie 使用
                        </h2>
                        <p className="text-center mt-3" />
                        我們的網站可能使用 cookie 技術來收集和存儲特定訊息。Cookie 是一種包含少量資訊的文字檔案，當您訪問網站時由網站傳送到您的瀏覽器。我們使用 cookie 來記錄您的偏好設置、改進使用者體驗和分析流量。您可以選擇接受或拒絕 cookie。如果您選擇拒絕 cookie，可能無法完全體驗我們網站的功能。
                        <h2>
                            第三方連結
                        </h2>
                        <p className="text-center mt-3" />
                        我們的網站可能包含指向其他網站的連結，這些網站遵循其自己的隱私權政策。我們對於這些連結網站的行為和內容不負責任。我們鼓勵您在離開我們的網站後閱讀其他網站的隱私權政策。
                        <h2>
                            隱私權政策的變更
                        </h2>
                        <p className="text-center mt-3" />
                        我們保留隨時修改本隱私權政策的權利。任何修改都將在本網站上公布。如您對我們的隱私權政策有任何疑問，請隨時與我們聯繫。
                    </div>
                </article>
            </Container>
        </Container>
    );
}

export default Privacy;