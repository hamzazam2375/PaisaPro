import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import PriceComparison from "./components/ui";
import SentimentAnalysisApp from "./components/ui2";
import FinancialAssistant from "./components/ui3";
import ShoppingCartOptimizer from './components/ui4';

function App() {
  return (
    <Router>
      <nav style={{ padding: "1rem", backgroundColor: "#1e293b" }}>
        <Link to="/" style={{ marginRight: "1rem", color: "#f1f5f9" }}>
          Price Compare
        </Link>
        <Link to="/sentiment" style={{ marginRight: "1rem", color: "#f1f5f9" }}>
          Sentiment Analysis
        </Link>
        <Link to="/financial" style={{ marginRight: "1rem", color: "#f1f5f9" }}>
          Financial Assistant
        </Link>
        <Link to="/cart" style={{ color: "#f1f5f9" }}>
          Shopping Cart
        </Link>
      </nav>

      <Routes>
        <Route path="/" element={<PriceComparison />} />
        <Route path="/sentiment" element={<SentimentAnalysisApp />} />
        <Route path="/financial" element={<FinancialAssistant />} />
        <Route path="/cart" element={<ShoppingCartOptimizer />} />
      </Routes>
    </Router>
  );
}

export default App;