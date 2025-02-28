// src/pages/Contact.jsx

import Header from '../components/Header';
import Footer from '../components/Footer';

const Contact = () => {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow container mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-6 text-center">Contact Us</h1>
        <form className="max-w-xl mx-auto bg-white p-6 rounded-lg shadow">
          <div className="mb-4">
            <label htmlFor="name" className="block text-gray-700 font-semibold mb-2">Name</label>
            <input type="text" id="name" className="w-full border border-gray-300 p-2 rounded" placeholder="Your Name" required />
          </div>
          <div className="mb-4">
            <label htmlFor="email" className="block text-gray-700 font-semibold mb-2">Email</label>
            <input type="email" id="email" className="w-full border border-gray-300 p-2 rounded" placeholder="Your Email" required />
          </div>
          <div className="mb-4">
            <label htmlFor="message" className="block text-gray-700 font-semibold mb-2">Message</label>
            <textarea id="message" className="w-full border border-gray-300 p-2 rounded" placeholder="Your Message" rows="5" required></textarea>
          </div>
          <button type="submit" className="w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded">Send Message</button>
        </form>
      </main>
      <Footer />
    </div>
  );
};

export default Contact;
