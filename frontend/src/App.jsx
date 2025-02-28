// src/App.jsx


import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Landing from './pages/Landing';
import TeacherLanding from './pages/TeacherLanding';
import StudentLanding from './pages/StudentLanding';
import About from './pages/About';
import Contact from './pages/Contact';

const router = createBrowserRouter([
  { path: '/', element: <Landing /> },
  { path: '/teacher', element: <TeacherLanding /> },
  { path: '/student', element: <StudentLanding /> },
  { path: '/about', element: <About /> },
  { path: '/contact', element: <Contact /> }, 
], {
  future: {
    v7_startTransition: true,
    v7_relativeSplatPath: true,
  },
});

function App() {
  return <RouterProvider router={router}  />;
}

export default App;