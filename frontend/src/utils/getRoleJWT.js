import { jwtDecode } from "jwt-decode";
import getCookie from "./token";

const getRoleFromAccessToken = () => {
  try {
    const token = getCookie("access");
    if (!token) return null;

    const decoded = jwtDecode(token);
    return decoded.role || null;
  } catch (error) {
    console.error("Ошибка при декодировании токена:", error);
    return null;
  }
};

export default getRoleFromAccessToken;
