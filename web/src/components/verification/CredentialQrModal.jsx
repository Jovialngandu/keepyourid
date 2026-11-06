import { useState } from "react";
import QRCode from "react-qr-code";

import { getCredentialQrValue } from "../../utils/verification";
import "../../styles/verification.css";

export default function CredentialQrModal({ credential, onClose }) {
  const value = getCredentialQrValue(credential);
  const [copied, setCopied] = useState(false);

  if (!value) {
    return null;
  }

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <div
      className="qr-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label="QR code de la credential"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="qr-modal">
        <button
          type="button"
          className="qr-modal-close"
          onClick={onClose}
          aria-label="Fermer le QR code"
        >
          ×
        </button>

        <span className="verification-eyebrow">QR DE VÉRIFICATION</span>
        <h2>Credential présentée</h2>

        <div className="qr-code-frame">
          <QRCode value={value} size={216} level="M" />
        </div>

        <div className="qr-modal-actions">
          <button
            type="button"
            className="qr-copy-button"
            onClick={handleCopy}
          >
            {copied ? "JSON copié" : "Copier le JSON"}
          </button>
        </div>

        <p>
          Ce QR code contient uniquement l'enveloppe{" "}
          <code>signed_credential</code>.
        </p>
      </div>
    </div>
  );
}
