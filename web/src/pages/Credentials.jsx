
import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  createCredential,
  getCredentials,
  revokeCredential,
} from "../services/credential";

const initialFields = [
  { key: "given_name", label: "Prénom", value: "" },
  { key: "family_name", label: "Nom", value: "" },
  { key: "date_of_birth", label: "Date de naissance", value: "" },
  { key: "place_of_birth", label: "Lieu de naissance", value: "" },
  { key: "nationality", label: "Nationalité", value: "Congolaise" },
  { key: "sex", label: "Sexe", value: "" },
  { key: "address", label: "Adresse", value: "" },
  { key: "document_number", label: "Numéro du document", value: "" },
];

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("fr-FR");
}

function statusLabel(status) {
  return {
    DRAFT: "Brouillon",
    ISSUED: "Émis",
    REVOKED: "Révoqué",
  }[status] || status || "Inconnu";
}

function statusClass(status) {
  return {
    DRAFT: "credential-status draft",
    ISSUED: "credential-status issued",
    REVOKED: "credential-status revoked",
  }[status] || "credential-status";
}

export default function Credentials() {
  const { organizationId } = useParams();

  const [credentials, setCredentials] = useState([]);
  const [fields, setFields] = useState(initialFields);
  const [validUntil, setValidUntil] = useState("");
  const [holderDid, setHolderDid] = useState("");
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showForm, setShowForm] = useState(false);

  const loadCredentials = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getCredentials(organizationId);
      setCredentials(Array.isArray(data) ? data : data?.items || []);
    } catch (err) {
      setError(err.message || "Impossible de charger les justificatifs.");
    } finally {
      setLoading(false);
    }
  }, [organizationId]);

  useEffect(() => {
    loadCredentials();
  }, [loadCredentials]);

  function updateField(index, property, value) {
    setFields((current) =>
      current.map((field, i) =>
        i === index ? { ...field, [property]: value } : field
      )
    );
  }

  function addField() {
    setFields((current) => [
      ...current,
      { key: "", label: "", value: "" },
    ]);
  }

  function removeField(index) {
    setFields((current) => current.filter((_, i) => i !== index));
  }

  function resetForm() {
    setFields(initialFields);
    setValidUntil("");
    setHolderDid("");
  }

  async function handleCreate(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (!holderDid.trim()) {
      setError("Le DID du titulaire doit être récupéré depuis son wallet.");
      return;
    }

    if (!validUntil) {
      setError("La date d'expiration est obligatoire.");
      return;
    }

    const subjectData = {};

    for (const field of fields) {
      const key = field.key.trim();
      if (!key) continue;

      if (Object.prototype.hasOwnProperty.call(subjectData, key)) {
        setError(`Le champ "${key}" est présent plusieurs fois.`);
        return;
      }

      subjectData[key] = field.value.trim();
    }

    if (!subjectData.given_name || !subjectData.family_name) {
      setError("Le prénom et le nom sont obligatoires.");
      return;
    }

    try {
      setCreating(true);

      await createCredential(organizationId, {
        credential_type: "IdentityCredential",
        subject: {
          id: holderDid.trim(),
          ...subjectData,
        },
        valid_until: new Date(validUntil).toISOString(),
      });

      resetForm();
      setShowForm(false);
      setSuccess("Le brouillon de la carte d'identité a été créé.");
      await loadCredentials();
    } catch (err) {
      setError(err.message || "La création du brouillon a échoué.");
    } finally {
      setCreating(false);
    }
  }

  async function handleRevoke(credentialId) {
    const reason = window.prompt(
      "Pourquoi souhaitez-vous révoquer ce justificatif ?"
    );

    if (!reason?.trim()) return;

    try {
      setError("");
      setSuccess("");

      await revokeCredential(organizationId, credentialId, reason.trim());

      setSuccess("Le justificatif a été révoqué.");
      await loadCredentials();
    } catch (err) {
      setError(err.message || "La révocation a échoué.");
    }
  }

  return (
    <main className="credentials-page">
      <div className="credentials-header">
        <div>
          <Link
            to={`/organizations/${organizationId}`}
            className="credentials-back"
          >
            ← Retour au tableau de bord
          </Link>

          <p className="credentials-eyebrow">ESPACE ÉMETTEUR</p>
          <h1>Justificatifs numériques</h1>
          <p className="credentials-description">
            Préparez et gérez les documents numériques délivrés par votre organisation.
          </p>
        </div>

        <button
          type="button"
          className="credentials-primary-button"
          onClick={() => {
            setShowForm((value) => !value);
            setError("");
            setSuccess("");
          }}
        >
          {showForm ? "Fermer" : "+ Nouvelle carte"}
        </button>
      </div>

      {error && <div className="credentials-alert error">{error}</div>}
      {success && <div className="credentials-alert success">{success}</div>}

      {showForm && (
        <section className="credentials-form-card">
          <div className="credentials-section-heading">
            <div>
              <p className="credentials-eyebrow">NOUVEAU DOCUMENT</p>
              <h2>Carte d'identité numérique</h2>
              <p>Renseignez les informations qui figureront dans le justificatif.</p>
            </div>
          </div>

          <form onSubmit={handleCreate} className="credentials-form">
            <div className="credentials-fields">
              {fields.map((field, index) => (
                <div className="credential-field-row" key={index}>
                  <label>
                    Clé
                    <input
                      value={field.key}
                      onChange={(e) =>
                        updateField(index, "key", e.target.value)
                      }
                      placeholder="ex. given_name"
                    />
                  </label>

                  <label>
                    Libellé
                    <input
                      value={field.label}
                      onChange={(e) =>
                        updateField(index, "label", e.target.value)
                      }
                      placeholder="ex. Prénom"
                    />
                  </label>

                  <label>
                    Valeur
                    <input
                      value={field.value}
                      onChange={(e) =>
                        updateField(index, "value", e.target.value)
                      }
                      placeholder="Saisir la valeur"
                    />
                  </label>

                  <button
                    type="button"
                    className="credentials-remove-field"
                    onClick={() => removeField(index)}
                    aria-label="Supprimer ce champ"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            <button
              type="button"
              className="credentials-secondary-button"
              onClick={addField}
            >
              + Ajouter un champ
            </button>

            <div className="credentials-wallet-section">
              <h3>Identité numérique du titulaire</h3>
              <p>
                Le DID devra être obtenu depuis le portefeuille du citoyen,
                après une preuve de contrôle de son identité numérique.
              </p>

              <label>
                DID du titulaire
                <input
                  value={holderDid}
                  onChange={(e) => setHolderDid(e.target.value)}
                  placeholder="DID récupéré depuis le wallet"
                  required
                />
              </label>
              <small>
                Connexion et récupération automatique depuis le wallet à intégrer.
              </small>
            </div>

            <label>
              Date d'expiration
              <input
                type="datetime-local"
                value={validUntil}
                onChange={(e) => setValidUntil(e.target.value)}
                required
              />
            </label>

            <div className="credentials-form-actions">
              <button
                type="button"
                className="credentials-secondary-button"
                onClick={() => {
                  resetForm();
                  setShowForm(false);
                }}
              >
                Annuler
              </button>

              <button
                type="submit"
                className="credentials-primary-button"
                disabled={creating}
              >
                {creating ? "Création..." : "Créer le brouillon"}
              </button>
            </div>
          </form>
        </section>
      )}

      <section className="credentials-list-section">
        <div className="credentials-section-heading">
          <div>
            <h2>Registre des justificatifs</h2>
            <p>{credentials.length} justificatif(s) enregistré(s)</p>
          </div>

          <button
            type="button"
            className="credentials-refresh"
            onClick={loadCredentials}
            disabled={loading}
          >
            Actualiser
          </button>
        </div>

        {loading ? (
          <div className="credentials-empty">Chargement...</div>
        ) : credentials.length === 0 ? (
          <div className="credentials-empty">
            <div className="credentials-empty-icon">◇</div>
            <h3>Aucun justificatif pour le moment</h3>
            <p>Les justificatifs créés apparaîtront ici.</p>
          </div>
        ) : (
          <div className="credentials-table-wrapper">
            <table className="credentials-table">
              <thead>
                <tr>
                  <th>Identifiant</th>
                  <th>Type</th>
                  <th>Titulaire</th>
                  <th>Expiration</th>
                  <th>État</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {credentials.map((credential) => (
                  <tr key={credential.id}>
                    <td className="credential-id">
                      {credential.id?.slice(0, 8) || "—"}
                    </td>
                    <td>
                      {credential.credential_type || "Justificatif"}
                    </td>
                    <td className="credential-holder">
                      {credential.credentialSubject?.id ||
                        credential.credential_subject?.id || "—"}
                    </td>
                    <td>
                      {formatDate(credential.valid_until || credential.validUntil)}
                    </td>
                    <td>
                      <span className={statusClass(credential.status)}>
                        {statusLabel(credential.status)}
                      </span>
                    </td>
                    <td>
                      {credential.status === "ISSUED" && (
                        <button
                          type="button"
                          className="credentials-revoke-button"
                          onClick={() => handleRevoke(credential.id)}
                        >
                          Révoquer
                        </button>
                      )}
                      {credential.status === "DRAFT" && (
                        <span className="credentials-pending">
                          En attente de signature
                        </span>
                      )}
                      {credential.status === "REVOKED" && (
                        <span className="credentials-pending">
                          Révoqué
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
