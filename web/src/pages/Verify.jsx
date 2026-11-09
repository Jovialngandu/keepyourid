import { useCallback, useState } from "react";

import Footer from "../components/layout/Footer";
import Navbar from "../components/layout/Navbar";
import QrScanner from "../components/verification/QrScanner";
import VerificationResult from "../components/verification/VerificationResult";
import {
  fetchCredentialPresentation,
  verifyCredential,
} from "../services/verification";
import { normalizeVerificationInput } from "../utils/verification";

import "../styles/verification.css";

function readFileAsText(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
}

export default function Verify() {
  const [scanning, setScanning] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const runVerification = useCallback(async (input) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      let payload = input;

      if (/^https?:\/\//i.test(String(input).trim())) {
        const data = await fetchCredentialPresentation(String(input).trim());
        payload = normalizeVerificationInput(JSON.stringify(data));
      } else {
        payload = normalizeVerificationInput(input);
      }

      const data = await verifyCredential(payload);
      setResult(data);
    } catch (err) {
      const isInvalid =
        err?.status === 422 ||
        err?.name === "SyntaxError" ||
        /non reconnu|vide|JSON valide/.test(err?.message || "");

      setError({
        kind: isInvalid ? "invalid" : "technical",
        message: err?.message || "Erreur inattendue pendant la vérification.",
        status: err?.status,
      });
    } finally {
      setLoading(false);
    }
  }, []);

  const handleScan = useCallback(
    (text) => {
      setScanning(false);
      runVerification(text);
    },
    [runVerification]
  );

  const handleScannerError = useCallback((message) => {
    setScanning(false);
    setError({
      kind: "technical",
      message: message || "Impossible d'utiliser la caméra.",
    });
  }, []);

  const handleFile = useCallback(
    async (event) => {
      const file = event.target.files?.[0];
      event.target.value = "";

      if (!file) return;

      try {
        const text = await readFileAsText(file);
        await runVerification(text);
      } catch (err) {
        setError({
          kind: "invalid",
          message: err?.message || "Fichier JSON non reconnu.",
        });
      }
    },
    [runVerification]
  );

  return (
    <>
      <Navbar />

      <main className="verification-page">
        <header className="verification-header">
          <span className="verification-eyebrow">VÉRIFICATION</span>
          <h1>Vérifiez une credential.</h1>
          <p>
            Scannez le QR code présenté par le titulaire ou importez le
            fichier JSON de la credential pour obtenir un verdict
            cryptographique.
          </p>
        </header>

        <section className="verification-grid">
          <article className="verification-card">
            <span className="verification-eyebrow">SCAN</span>
            <h2>Scanner un QR code</h2>
            <p>
              La caméra lit l'enveloppe{" "}
              <code>signed_credential</code> et l'envoie au service de
              vérification.
            </p>

            <button
              type="button"
              className="verification-button"
              onClick={() => setScanning(true)}
              disabled={loading || scanning}
            >
              Ouvrir la caméra
            </button>
          </article>

          <article className="verification-card">
            <span className="verification-eyebrow">IMPORT</span>
            <h2>Importer un fichier JSON</h2>
            <p>
              Utilisez le fichier exporté par le wallet ou le JSON signé
              de la credential.
            </p>

            <label className="verification-file-label">
              Choisir un fichier
              <input
                type="file"
                accept=".json,application/json"
                onChange={handleFile}
                disabled={loading}
                data-testid="verification-file-input"
              />
            </label>
          </article>
        </section>

        {scanning && (
          <QrScanner
            onScan={handleScan}
            onError={handleScannerError}
            onClose={() => setScanning(false)}
          />
        )}

        <VerificationResult
          loading={loading}
          result={result}
          error={error}
        />
      </main>

      <Footer />
    </>
  );
}
