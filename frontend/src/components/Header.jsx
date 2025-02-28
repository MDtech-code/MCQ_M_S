// src/components/Header.jsx

import { Link } from 'react-router-dom';

const Header = () => {
  return (
    <header className="bg-white shadow">
      <div className="container mx-auto flex items-center justify-between py-4 px-6">
        <Link to="/" className="text-2xl font-bold text-gray-800">MCQ_M_S</Link>
        <nav className="space-x-4">
          <Link to="/" className="text-gray-600 hover:text-gray-800">Home</Link>
          <Link to="/about" className="text-gray-600 hover:text-gray-800">About</Link>
          <Link to="/contact" className="text-gray-600 hover:text-gray-800">Contact</Link>
          <Link to="/login" className="text-gray-600 hover:text-gray-800">Login</Link>
          <Link to="/register" className="text-gray-600 hover:text-gray-800">Register</Link>
        </nav>
      </div>
    </header>
  );
};

export default Header;
