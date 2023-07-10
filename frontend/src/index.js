import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Header from "./components/Header";
import Home from './Home';
import Category from './Category';
import About from './components/About';
import Footer from './components/Footer';
import SearchResult from './components/SearchResult';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <Header />
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/瀏覽分類" element={<Category />} />
        <Route path="/關於我們" element={<About />} />
        <Route path="/s/" element={<SearchResult />} />
      </Routes>
    </BrowserRouter>
    <Footer />
  </React.StrictMode >
);
