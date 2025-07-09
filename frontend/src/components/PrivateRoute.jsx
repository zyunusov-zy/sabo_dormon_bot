import { Navigate } from 'react-router-dom';

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  return parts.length === 2 ? parts.pop().split(';').shift() : null;
}

export default function PrivateRoute({ children }) {
  const access = getCookie('access');
  return access ? children : <Navigate to="/login" />;
}
