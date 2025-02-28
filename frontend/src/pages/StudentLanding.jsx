// src/pages/StudentLanding.jsx

import Header from '../components/Header';
import Footer from '../components/Footer';
import { Link } from 'react-router-dom';

const StudentLanding = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow">
        {/* Hero Section for Students */}
        <section className="relative">
          <img 
            src="https://source.unsplash.com/random/1600x900/?student,study" 
            alt="Student" 
            className="w-full h-96 object-cover"
          />
          <div className="absolute inset-0 bg-green-900 opacity-50"></div>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-white">
            <h1 className="text-4xl md:text-6xl font-bold">Ace Your Exams</h1>
            <p className="mt-4 text-lg md:text-2xl">Take personalized tests and track your progress with real-time feedback.</p>
            <div className="mt-6">
              <Link to="/register" className="bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded">Get Started as a Student</Link>
            </div>
          </div>
        </section>
        {/* Benefits Section */}
        <section className="py-12 bg-gray-100">
          <div className="container mx-auto px-6">
            <h2 className="text-3xl font-bold text-center mb-8">Why Choose MCQ_M_S?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Personalized Tests</h3>
                <p className="text-gray-600">Receive tests that adapt to your learning curve and focus on your weak areas.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Real-Time Feedback</h3>
                <p className="text-gray-600">Understand your performance instantly with detailed feedback.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Track Your Progress</h3>
                <p className="text-gray-600">Monitor your improvement over time with comprehensive analytics.</p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default StudentLanding;
