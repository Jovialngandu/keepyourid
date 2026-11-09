import { Link } from "react-router-dom";

import Navbar from "../components/layout/Navbar";
import Footer from "../components/layout/Footer";

import "../styles/not-found.css";

export default function NotFound() {
  return (
    <>
      <Navbar />

      <main className="not-found">
        <div className="not-found-card">
          <span className="not-found-eyebrow">ERREUR 404</span>

          <h1>Cette page n'existe pas.</h1>

          <p>
            L'adresse que vous cherchez est introuvable ou a été déplacée.
            Retournez à l'accueil ou vérifiez une credential en attendant.
          </p>

          <div className="not-found-actions">
            <Link to="/" className="not-found-button not-found-button-primary">
              Retour à l'accueil
            </Link>
            <Link to="/verify" className="not-found-button">
              Vérifier une credential
            </Link>
            <Link to="/help" className="not-found-button">
              Consulter le guide
            </Link>
          </div>
        </div>
      </main>

      <Footer />
    </>
  );
}
