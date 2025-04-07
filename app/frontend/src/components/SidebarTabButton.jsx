// src/components/SidebarTabButton.jsx
export default function SidebarTabButton({ isActive, onClick, children }) {
  return (
    <button
      className={`w-full text-left px-3 py-2 rounded transition-colors duration-200 ${
        isActive
          ? "bg-gray-700 text-white"
          : "bg-gray-800 text-gray-300 hover:bg-gray-700"
      }`}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

