
import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { createCredential } from "../services/credential";
import "../styles/credential.css";
const credentialTypes = [
  "IdentityCredential",
  "UniversityDegreeCredential",
  "ProfessionalCredential",
  "StudentCredential",
  "CertificateCredential",
];

export default function CredentialCreate() {
  const { organizationId } = useParams();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    holderDid: "",
    credentialType: "IdentityCredential",
    validUntil: "",
    attributes: '{\n  "documentNumber": ""\n}',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");

    let attributes;

    try {
      attributes = JSON.parse(form.attributes || "{}");
    } catch {
      setError("Les attributs doivent contenir un JSON valide.");
      return;
    }

    if (
      !attributes ||
      typeof attributes !== "object" ||
      Array.isArray(attributes)
    ) {
      setError("Les attributs doivent être un objet JSON.");
      return;
    }

    const subject = {
      name: `${form.firstName.trim()} ${form.lastName.trim()}`.trim(),
      firstName: form.firstName.trim(),
      lastName: form.lastName.trim(),
      email: form.email.trim() || undefined,
      ...attributes,
    };

    if (form.holderDid.trim()) {
      subject.id = form.holderDid.trim();
    }

    const payload = {
      credential_type: form.credentialType,
      subject,
      ...(form.validUntil
        ? {
            valid_until: new Date(
              `${form.validUntil}T23:59:59`
            ).toISOString(),
          }
        : {}),
    };

    try {
      setLoading(true);

      const result = await createCredential(
        organizationId,
        payload
      );

      const credentialId =
        result?.id ??
        result?.credential_id ??
        result?.credential?.id;

      if (!credentialId) {
        throw new Error(
          "Le credential a été créé, mais son identifiant est absent de la réponse API."
        );
      }

      navigate(
        `/organizations/${organizationId}/credentials/${credentialId}`
      );
    } catch (err) {
      setError(err.message || "Impossible de créer le credential.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page-container">
      <div className="page-heading">
        <button
          type="button"
          className="back-button"
          onClick={() => navigate(-1)}
        >
          ← Retour
        </button>

        <p className="eyebrow">PORTAIL ÉMETTEUR</p>
        <h1>Délivrer une identité</h1>
        <p>
          Enregistrez les informations du titulaire et préparez
          son identité vérifiable.
        </p>
      </div>

      <form className="credential-form" onSubmit={handleSubmit}>
        <section className="form-section">
          <h2>Informations du titulaire</h2>
          <p>
            Identifiez la personne à laquelle l'organisation
            souhaite délivrer une identité.
          </p>

          <div className="form-grid">
            <label>
              Prénom *
              <input
                required
                value={form.firstName}
                onChange={(e) =>
                  update("firstName", e.target.value)
                }
                placeholder="Jean"
              />
            </label>

            <label>
              Nom *
              <input
                required
                value={form.lastName}
                onChange={(e) =>
                  update("lastName", e.target.value)
                }
                placeholder="Dupont"
              />
            </label>

            <label>
              Adresse e-mail
              <input
                type="email"
                value={form.email}
                onChange={(e) =>
                  update("email", e.target.value)
                }
                placeholder="jean@example.com"
              />
            </label>

            <label>
              DID du titulaire
              <input
                value={form.holderDid}
                onChange={(e) =>
                  update("holderDid", e.target.value)
                }
                placeholder="did:ethr:sepolia:..."
              />
              <small>
                Facultatif si le titulaire n'a pas encore de DID.
              </small>
            </label>
          </div>
        </section>

        <section className="form-section">
          <h2>Identité à délivrer</h2>

          <label>
            Type de credential *
            <select
              value={form.credentialType}
              onChange={(e) =>
                update("credentialType", e.target.value)
              }
            >
              {credentialTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>

          <label>
            Date d'expiration
            <input
              type="date"
              value={form.validUntil}
              min={new Date().toISOString().slice(0, 10)}
              onChange={(e) =>
                update("validUntil", e.target.value)
              }
            />
          </label>

          <label>
            Attributs supplémentaires (JSON)
            <textarea
              rows={7}
              value={form.attributes}
              onChange={(e) =>
                update("attributes", e.target.value)
              }
              spellCheck="false"
            />
            <small>
              Exemple : numéro de document, établissement,
              spécialité, date d'obtention...
            </small>
          </label>
        </section>

        {error && (
          <div className="form-error" role="alert">
            {error}
          </div>
        )}

        <div className="form-actions">
          <button
            type="button"
            className="button-secondary"
            onClick={() => navigate(-1)}
            disabled={loading}
          >
            Annuler
          </button>

          <button
            type="submit"
            className="button-primary"
            disabled={loading}
          >
            {loading ? "Création..." : "Créer le credential"}
          </button>
        </div>
      </form>
    </main>
  );
}
