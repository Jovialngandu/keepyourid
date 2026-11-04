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

          <span className="eyebrow">ORGANIZATION CREATED</span>

          <h1>You're in.</h1>

          <p>Your organization has been registered successfully.</p>

          <div className="organization-summary">
            <span>Organization</span>
            <strong>{organization.legal_name}</strong>

            <span>Registration number</span>
            <strong>{organization.registration_number}</strong>

            <span>Status</span>
            <strong>{organization.status}</strong>
          </div>

          <p className="success-note">
            Your organization is registered. The next step is to
            associate and verify its digital identity.
          </p>

          <button
            type="button"
            className="registration-button"
            onClick={() => navigate(`/organizations/${organization.id}`)}
          >
            Continue <span>→</span>
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
          <span className="eyebrow">GET STARTED</span>

          <h1>Register your organization.</h1>

          <p>
            Start by providing your organization's legal information.
            You will be able to associate its digital identity next.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-field">
            <label htmlFor="legal_name">Legal name</label>
            <input
              id="legal_name"
              name="legal_name"
              value={form.legal_name}
              onChange={handleChange}
              placeholder="Your organization's legal name"
              minLength={2}
              maxLength={255}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="registration_number">
              Registration number
            </label>
            <input
              id="registration_number"
              name="registration_number"
              value={form.registration_number}
              onChange={handleChange}
              placeholder="Official registration number"
              maxLength={100}
              required
            />
          </div>

          <div className="form-field">
            <label htmlFor="email">Organization email</label>
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
              Phone number <span>Optional</span>
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
            {loading ? "Registering..." : "Create organization"}
            {!loading && <span>→</span>}
          </button>
        </form>

        <p className="registration-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}

export default OrganizationRegister;