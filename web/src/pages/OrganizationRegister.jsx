import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createOrganization } from "../services/api";
import "../styles/organization-register.css";

const initialForm = {
  legal_name: "",
  registration_number: "",
  email: "",
  phone: "",
};

function OrganizationRegister() {
  const [form, setForm] = useState(initialForm);
  const [organization, setOrganization] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      const payload = {
        ...form,
        legal_name: form.legal_name.trim(),
        registration_number: form.registration_number.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || null,
      };

      const result = await createOrganization(payload);

      if (!result?.id) {
        throw new Error("L'API n'a pas retourné l'identifiant de l'organisation.");
      }

      setOrganization(result);

      // Navigate using the ID returned directly by the API.
      navigate(`/organizations/${result.id}`);
    } catch (err) {
      setError(err.message || "Une erreur est survenue.");
    } finally {
      setLoading(false);
    }
  }

  if (organization) {
    return (
      <main className="registration-page">
        <section className="registration-card success-card">
          <div className="success-icon">✓</div>

          <span className="eyebrow">ORGANISATION CRÉÉE</span>

          <h1>C'est fait.</h1>

          <p>Votre organisation a été enregistrée avec succès.</p>

          <div className="organization-summary">
            <span>Organisation</span>
            <strong>{organization.legal_name}</strong>

            <span>Numéro d'enregistrement</span>
            <strong>{organization.registration_number}</strong>

            <span>Statut</span>
            <strong>{organization.status}</strong>
          </div>

          <p className="success-note">
            Votre organisation est enregistrée. L'étape suivante consiste
            à associer et vérifier son identité numérique.
          </p>

          <button
            type="button"
            className="registration-button"
            onClick={() => navigate(`/organizations/${organization.id}`)}
          >
            Continuer <span>→</span>
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="registration-page">
      <section className="registration-card">
        <Link to="/" className="brand">
          keepyourid<span>.</span>
        </Link>

        <div className="registration-heading">
          <span className="eyebrow">POUR COMMENCER</span>

          <h1>Enregistrez votre organisation.</h1>

          <p>
            Commencez par renseigner les informations légales de votre
            organisation. Vous pourrez ensuite associer son identité
            numérique.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="legal_name">Raison sociale</label>
            <input
              id="legal_name"
              name="legal_name"
              value={form.legal_name}
              onChange={handleChange}
              placeholder="Raison sociale de l'organisation"
              minLength={2}
              maxLength={255}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="registration_number">
              Numéro d'enregistrement
            </label>
            <input
              id="registration_number"
              name="registration_number"
              value={form.registration_number}
              onChange={handleChange}
              placeholder="Numéro d'enregistrement officiel"
              maxLength={100}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="email">Email de l'organisation</label>
            <input
              id="email"
              name="email"
              type="email"
              value={form.email}
              onChange={handleChange}
              placeholder="contact@organization.com"
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="phone">
              Téléphone <span>Facultatif</span>
            </label>
            <input
              id="phone"
              name="phone"
              type="tel"
              value={form.phone}
              onChange={handleChange}
              placeholder="+243 ..."
              maxLength={30}
            />
          </div>

          {error && (
            <div className="form-error" role="alert">
              {error}
            </div>
          )}

          <button
            type="submit"
            className="registration-button"
            disabled={loading}
          >
            {loading ? "Enregistrement..." : "Créer l'organisation"}
            {!loading && <span>→</span>}
          </button>
        </form>

        <p className="registration-footer">
          Déjà un compte ? <Link to="/login">Se connecter</Link>
        </p>
      </section>
    </main>
  );
}

export default OrganizationRegister;