
import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { DEMO_ACCOUNT } from "../data/demo";

function Register() {
  const { register, login, user, loading } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);

  if (loading) return <div className="page-loading">Chargement...</div>;
  if (user) return <Navigate to="/organizations" replace />;

  async function handleDemoLogin() {
    setError("");
    setDemoLoading(true);

    try {
      await login(DEMO_ACCOUNT);
      navigate("/organizations", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setDemoLoading(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);

    try {
      // Registration now returns a session (access_token) directly.
      await register({
        full_name: fullName,
        email,
        password,
      });

      navigate("/organizations", { replace: true });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <Link to="/" className="auth-brand">keepyourid.</Link>

        <h1>Créez votre compte</h1>
        <p>Créez votre compte pour accéder à KeepYourID.</p>

        <form onSubmit={handleSubmit}>
          <label htmlFor="fullName">Nom complet</label>
          <input
            id="fullName"
            type="text"
            autoComplete="name"
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            minLength={2}
            maxLength={255}
            required
          />

          <label htmlFor="email">Adresse email</label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />

          <label htmlFor="password">Mot de passe</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            minLength={8}
            maxLength={128}
            required
          />

          {error && <p className="form-error">{error}</p>}

          <button type="submit" disabled={submitting}>
            {submitting ? "Création..." : "Créer mon compte"}
          </button>
        </form>

        <p>
          Déjà inscrit ? <Link to="/login">Se connecter</Link>
        </p>

        <button
          type="button"
          className="demo-login-button"
          onClick={handleDemoLogin}
          disabled={submitting || demoLoading}
        >
          {demoLoading
            ? "Connexion au compte de test..."
            : "Essayer le compte de test"}
        </button>
      </section>
    </main>
  );
}

export default Register;
