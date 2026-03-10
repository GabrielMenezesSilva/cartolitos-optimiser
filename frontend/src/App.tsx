import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Optimiser from './pages/Optimiser';
import Layout from './components/Layout';

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/optimiser" replace />} />
          <Route path="/optimiser" element={<Layout><Optimiser /></Layout>} />
          <Route path="*" element={<Navigate to="/optimiser" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
