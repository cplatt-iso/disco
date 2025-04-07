// src/pages/Login.jsx
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/UserContext";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();
  const { login } = useAuth();

  const tileSize = 100;
  const discoColors = [
    "#FF0080",
    "#00FFFF",
    "#FFFF00",
    "#FF8C00",
    "#8A2BE2",
    "#00FF00",
    "#FF0000",
    "#00CED1",
  ];

  const [cols, setCols] = useState(20);
  const [rows, setRows] = useState(20);
  const [tiles, setTiles] = useState([]);

  useEffect(() => {
    const updateDimensions = () => {
      const newCols = Math.ceil(window.innerWidth / tileSize);
      const newRows = Math.ceil(window.innerHeight / tileSize);
      setCols(newCols);
      setRows(newRows);
      setTiles(
        Array.from({ length: newCols * newRows }, () =>
          discoColors[Math.floor(Math.random() * discoColors.length)]
        )
      );
    };

    updateDimensions();
    window.addEventListener("resize", updateDimensions);
    return () => window.removeEventListener("resize", updateDimensions);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setTiles((prev) =>
        prev.map(
          () => discoColors[Math.floor(Math.random() * discoColors.length)]
        )
      );
    }, 600);
    return () => clearInterval(interval);
  }, [cols, rows]);

  const handleLogin = (e) => {
    e.preventDefault();
    if (username === "admin" && password === "password") {
      login();
      navigate("/dashboard");
    } else {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden">
      <div
        className="absolute top-0 left-0 w-full h-full z-0"
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, ${tileSize}px)`,
          gridTemplateRows: `repeat(${rows}, ${tileSize}px)`,
        }}
      >
        {tiles.map((color, i) => (
          <div
            key={i}
            style={{
              width: `${tileSize}px`,
              height: `${tileSize}px`,
              backgroundColor: color,
            }}
          />
        ))}
      </div>

      <div className="absolute inset-0 flex items-center justify-center z-10">
        <form
          onSubmit={handleLogin}
          className="bg-white/80 backdrop-blur-md p-6 rounded-xl shadow-xl w-80 border border-white/30"
        >
          <h2 className="text-2xl font-bold text-center mb-4">DISCO Login</h2>
          <input
            className="w-full mb-3 p-2 border border-gray-300 rounded"
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="w-full mb-4 p-2 border border-gray-300 rounded"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="w-full bg-pink-600 text-white font-semibold py-2 rounded hover:bg-pink-700">
            Login
          </button>
        </form>
      </div>
    </div>
  );
}
