import '../css/Statement.css';
import Container from 'react-bootstrap/Container';

function Statement() {
    return (
        <div>
            <Container fluid="auto" className='statement-container-auto'>
                <Container fluid='md' className='statement-container-md'>
                    <div className='statement'>
                        <p>
                            ※ 本服務提供之商品價格 、漲跌紀錄等資訊皆為自動化程式蒐集，可能因各種不可預期之狀況而影響正確性或完整性， 僅供使用者參考之用，本服務不負任何擔保責任。
                        </p>
                        <p>
                            ※ 購買前請以購買當時銷售頁面資料為準自行判斷，該等資訊亦不得作為向第三人為任何主張之依據，包括但不限於：主張市場上有其他更優惠價格之補償或其他請求。
                        </p>
                    </div>
                </Container>
            </Container>
        </div >
    );
}

export default Statement;