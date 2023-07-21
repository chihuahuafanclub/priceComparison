import '../css/About.css';
import Container from 'react-bootstrap/Container';

function About() {
    return (
        <Container fluid="auto" className='about-container-auto'>
            <Container fluid='md' className='about-container-md'>
                <article>
                    <h1 className='text-center'>關於我們</h1>
                    <div className="about-article">
                        <p className='text-center mt-3' />
                        【比奇寶】  集天馬行空與購物樂趣於一身的奇幻購物之旅！
                        <p className='text-center mt-3' />
                        由嗜好古怪、樂於冒險的兩位魔法師們組成了"比奇寶"團隊。
                        <p className='text-center mt-3' />
                        旨在為你提供最神奇、最令人驚艷的購物體驗。魔法咒語能夠讓你在眨眼間找到你想要的商品，無需奔波，無需魔杖揮舞。
                        <p className='text-center mt-3' />
                        【比奇寶】  的產品特點：
                        魔法般快速、精準的搜索技術：轉眼間，你就能找到你的心儀寶物。
                        包羅萬象的網上商城商品：所有商城的商品一覽無遺，只需一站式購物體驗。
                    </div>
                </article>
            </Container>
        </Container>
    );
}

export default About;