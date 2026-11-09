import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../../context/AuthContext";
import { createOrganization } from "../../services/api";
import { DEMO_ACCOUNT } from "../../data/demo";

import "../../styles/demo.css";

const DEMO_PASSWORD = "123456789";

function randomSuffix() {
  return Math.random().toString(36).slice(2, 8);
}

export default function DemoAccess() {
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [generated, setGenerated] = useState(null);

  async function handleTestLogin() {
    setBusy("test");
    setError("");

    try {
      await login(DEMO_ACCOUNT);
      navigate("/organizations", { replace: true });
    } catch (err) {
      setError(err.message || "Connexion impossible.");
      setBusy("");
    }
  }

  async function handleRandomUser() {
    setBusy("random");
    setError("");
    setGenerated(null);

    const suffix = randomSuffix();
    const email = `demo${suffix}keepyourid@gmail.com`;
    const fullName = `Utilisateur Démo ${suffix}`;
    const orgName = `Organisation Démo ${suffix}`;

    try {
      await register({
        full_name: fullName,
        email,
        password: DEMO_PASSWORD,
      });

      await createOrganization({
        legal_name: orgName,
        registration_number: `DEMO-${suffix.toUpperCase()}`,
        email,
      });

      setGenerated({ email, orgName });
    } catch (err) {
      setError(err.message || "Création du compte de démonstration impossible.");
    } finally {
      setBusy("");
    }
  }

  return (
    <section className="demo-bar">
      <div className="demo-bar-content">
        <div>
          <span className="demo-eyebrow">ESPACE DÉMONSTRATION</span>
          <p>
            Testez la plateforme sans créer de compte : utilisez le compte
            de test ou générez un utilisateur aléatoire déjà équipé d'une
            organisation.
          </p>
        </div>

        <div className="demo-actions">
          <button
            type="button"
            className="demo-button demo-button-primary"
            onClick={handleTestLogin}
            disabled={Boolean(busy)}
          >
            {busy === "test" ? "Connexion..." : "Compte de test"}
          </button>

          <button
            type="button"
            className="demo-button"
            onClick={handleRandomUser}
            disabled={Boolean(busy)}
          >
            {busy === "random" ? "Création..." : "Générer un utilisateur"}
          </button>
        </div>
      </div>

      {error && <p className="demo-error">{error}</p>}

      {generated && (
        <div className="demo-result">
          <strong>Compte de démonstration créé</strong>

          <p>
            Email : <code>{generated.email}</code> · Mot de passe :{" "}
            <code>{DEMO_PASSWORD}</code>
          </p>

          <p>
            Une organisation ({generated.orgName}) a été créée pour ce
            compte. Pour la suite, connectez un <strong>wallet de
            test</strong> (compte de démonstration) — celui-ci servira à la
            fois pour le titulaire et pour l'émetteur.
          </p>

          <Link to="/wallet" className="demo-button demo-button-primary">
            Ouvrir mon wallet <span>→</span>
          </Link>
        </div>
      )}
    </section>
  );
}
