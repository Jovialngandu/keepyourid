import { useEffect } from "react";

const CHECK_LABELS = {
  signature: "Signature",
  issuer_did: "DID de l'émetteur",
  issuer_trust: "Confiance de l'émetteur",
  revocation: "Révocation",
  expiration: "Expiration",
};

function checkStatus(value) {
  if (value === true) {
    return { label: "Réussi", className: "check-ok" };
  }

  if (value === false) {
    return { label: "Échoué", className: "check-fail" };
  }

  if (value === "unknown") {
    return { label: "Inconnu", className: "check-unknown" };
  }

  return { label: "Non applicable", className: "check-na" };
}

export default function VerificationResult({ result, error, loading }) {
  useEffect(() => {
    const messages =
      result && Array.isArray(result.errors) ? result.errors : [];
    messages.forEach((message) => console.warn(message));
  }, [result]);

  if (loading) {
    return (
      <section className="verification-result verification-result-loading">
        Vérification en cours...
      </section>
    );
  }

  if (error) {
    const title =
      error.kind === "invalid" ? "Entrée invalide" : "Erreur technique";

    return (
      <section className="verification-result verification-result-error">
        <span className="verification-eyebrow">RÉSULTAT</span>
        <h2>{title}</h2>
        <p>{error.message}</p>
        {error.status && <small>Code HTTP : {error.status}</small>}
      </section>
    );
  }

  if (!result) {
    return null;
  }

  const checks = Object.entries(result.checks || {});

  return (
    <section className="verification-result">
      <span className="verification-eyebrow">RÉSULTAT</span>

      <h2
        className={
          result.valid
            ? "verification-verdict verification-verdict-success"
            : "verification-verdict verification-verdict-failed"
        }
      >
        {result.valid
          ? "Vérification réussie"
          : "Vérification échouée"}
      </h2>

      <div className="verification-meta">
        <div>
          <span>Credential ID</span>
          <strong>{result.credential_id || "Non fourni"}</strong>
        </div>

        <div>
          <span>Émetteur</span>
          <strong>{result.issuer || "Non fourni"}</strong>
        </div>
      </div>

      {checks.length > 0 && (
        <div className="verification-checks">
          {checks.map(([key, value]) => {
            const status = checkStatus(value);

            return (
              <div className="verification-check" key={key}>
                <span>{CHECK_LABELS[key] || key}</span>
                <strong className={status.className}>
                  {status.label}
                </strong>
              </div>
            );
          })}
        </div>
      )}

    </section>
  );
}
