// src/pages/TeacherLanding.jsx

import Header from '../components/Header';
import Footer from '../components/Footer';
import { Link } from 'react-router-dom';

const TeacherLanding = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow">
        {/* Hero Section for Teachers */}
        <section className="relative">
          <img 
            src="https://source.unsplash.com/random/1600x900/?teacher,education" 
            alt="Teacher" 
            className="w-full h-96 object-cover"
          />
          <div className="absolute inset-0 bg-blue-900 opacity-50"></div>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-white">
            <h1 className="text-4xl md:text-6xl font-bold">Transform Your Teaching</h1>
            <p className="mt-4 text-lg md:text-2xl">Easily create tests and track student performance.</p>
            <div className="mt-6">
              <Link to="/register" className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded">Get Started as a Teacher</Link>
            </div>
          </div>
        </section>
        {/* Benefits Section */}
        <section className="py-12 bg-gray-100">
          <div className="container mx-auto px-6">
            <h2 className="text-3xl font-bold text-center mb-8">Why Teach with MCQ_M_S?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Effortless Test Creation</h3>
                <p className="text-gray-600">Create tests quickly using our intuitive interface and auto-generated questions.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Insightful Analytics</h3>
                <p className="text-gray-600">Access detailed reports and analytics to monitor student progress.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Secure and Scalable</h3>
                <p className="text-gray-600">Rely on a robust platform designed to support your teaching needs.</p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default TeacherLanding;
