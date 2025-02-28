// src/pages/About.jsx

import Header from '../components/Header';
import Footer from '../components/Footer';

const About = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow container mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-6 text-center">About MCQ_M_S</h1>
        <p className="text-lg text-gray-700 mb-4">
          MCQ_M_S is a cutting-edge platform designed to revolutionize the way tests are created and taken. Whether you’re a teacher looking to streamline test creation or a student aiming to track your progress, our system offers adaptive testing, automatic MCQ generation, and real-time feedback.
        </p>
        <p className="text-lg text-gray-700 mb-4">
          Our mission is to empower both educators and learners with innovative tools that simplify the assessment process while providing valuable insights into performance and progress.
        </p>
        <p className="text-lg text-gray-700">
          We continually update our platform with the latest technologies to ensure that you have the best possible experience. Join us on this journey to transform education and make learning more engaging and effective.
        </p>
      </main>
      <Footer />
    </div>
  );
};

export default About;
