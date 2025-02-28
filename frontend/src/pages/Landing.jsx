// src/pages/Landing.jsx
import { Link } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';

const Landing = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow">
        {/* Hero Section */}
        <section className="relative">
          <img 
            src="https://source.unsplash.com/random/1600x900/?education" 
            alt="Education" 
            className="w-full h-96 object-cover"
          />
          <div className="absolute inset-0 bg-black opacity-50"></div>
          <div className="absolute inset-0 flex flex-col items-center justify-center text-center text-white">
            <h1 className="text-4xl md:text-6xl font-bold">Empower Your Learning Experience</h1>
            <p className="mt-4 text-lg md:text-2xl">Adaptive tests, real-time feedback, and more!</p>
            <div className="mt-6 space-x-4">
              <Link to="/teacher" className="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded">For Teachers</Link>
              <Link to="/student" className="bg-green-500 hover:bg-green-600 text-white py-2 px-4 rounded">For Students</Link>
            </div>
          </div>
        </section>
        {/* Overview Section */}
        <section className="py-12 bg-gray-100">
          <div className="container mx-auto px-6">
            <h2 className="text-3xl font-bold text-center mb-8">Why Choose MCQ_M_S?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Adaptive Testing</h3>
                <p className="text-gray-600">Get personalized tests based on your performance.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Automatic MCQ Generation</h3>
                <p className="text-gray-600">Generate questions effortlessly using advanced NLP.</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-semibold mb-2">Real-Time Feedback</h3>
                <p className="text-gray-600">Instant results to help you learn and improve.</p>
              </div>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default Landing;
