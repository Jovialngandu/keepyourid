import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../../context/AuthContext";

function Navbar() {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);

    try {
      await logout();
      navigate("/login", { replace: true });
    } catch (error) {
      console.error("Erreur lors de la déconnexion :", error);
    } finally {
      setLoggingOut(false);
    }
  }

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        keepyourid<span>.</span>
      </Link>

      <nav className="nav-links">
        <a href="/#product">Produit</a>
        <a href="/#solutions">Solutions</a>
        <a href="/#technology">Technologie</a>
      </nav>

      <div className="nav-actions">
        {isAuthenticated ? (
          <>
            <Link to="/wallet" className="nav-button">
              Mon Wallet
            </Link>

            <Link to="/organizations" className="nav-button">
              Organisations
            </Link>

            <span className="nav-user">
              {user?.full_name || user?.email}
            </span>

            <button
              type="button"
              className="nav-logout"
              onClick={handleLogout}
              disabled={loggingOut}
            >
              {loggingOut ? "Déconnexion..." : "Déconnexion"}
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="nav-login">
              Connexion
            </Link>

            <Link to="/register" className="nav-button">
              Get started <span>↗</span>
            </Link>
          </>
        )}
      </div>
    </header>
  );
}

export default Navbar;