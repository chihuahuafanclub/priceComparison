import "bootstrap/dist/css/bootstrap.min.css";
import "./css/index.css"
import React, { useState } from "react";
import Container from "react-bootstrap/Container";
import Form from "react-bootstrap/Form";
import Button from "react-bootstrap/Button";

function Contact() {
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [feedback, setFeedback] = useState("");

    const handleSubmit = (event) => {
        event.preventDefault();
    };

    return (
        <Container fluid="auto" className="contact-container-auto">
            <Container fluid="md" className="contact-container-md">
                <article>
                    <h1>意見反映</h1>
                    <div className="form-article">
                        <Form onSubmit={handleSubmit}>
                            <Form.Group controlId="name" className="form">
                                <Form.Label>姓名：</Form.Label>
                                <Form.Control
                                    type="text"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                />
                            </Form.Group>
                            <Form.Group controlId="email" className="form">
                                <Form.Label>電子郵件：</Form.Label>
                                <Form.Control
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                />
                            </Form.Group>
                            <Form.Group controlId="feedback" className="form">
                                <Form.Label>意見反饋：</Form.Label>
                                <Form.Control
                                    as="textarea"
                                    rows={4}
                                    value={feedback}
                                    onChange={(e) => setFeedback(e.target.value)}
                                    required
                                />
                            </Form.Group>
                            <Button type="submit">提交意見</Button>
                        </Form>
                    </div>
                </article>
            </Container>
        </Container>
    )
}

export default Contact;