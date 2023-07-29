import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Home from "./pages/home";
import Category from "./pages/category";
import About from "./pages/about";
import Privacy from "./pages/privacy"
import SearchResult from "./pages/searchresult";
import Contact from "./pages/contact";
import Footer from "./components/Footer";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <Header />
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/瀏覽分類" element={<Category />} />
        <Route path="/關於我們" element={<About />} />
        <Route path="/隱私權政策" element={<Privacy />} />
        <Route path="/s/" element={<SearchResult />} />
        <Route path="/意見反映" element={<Contact />} />
      </Routes>
    </BrowserRouter>
    <Footer />
  </React.StrictMode >
);
