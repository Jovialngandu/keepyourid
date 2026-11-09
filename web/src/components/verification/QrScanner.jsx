import { useEffect, useRef, useState } from "react";
import { BrowserQRCodeReader } from "@zxing/browser";
import { DecodeHintType } from "@zxing/library";

import "../../styles/verification.css";

export default function QrScanner({ onScan, onError, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const frameRef = useRef(null);
  const scannedRef = useRef(false);

  const onScanRef = useRef(onScan);
  const onErrorRef = useRef(onError);

  const [cameraError, setCameraError] = useState("");
  const [debugEnabled] = useState(
    () =>
      typeof window !== "undefined" &&
      new URLSearchParams(window.location.search).has("debug")
  );
  const [debugStats, setDebugStats] = useState({ attempts: 0, lastError: "" });
  const attemptsRef = useRef(0);
  const lastErrorRef = useRef("");
  const lastUiUpdateRef = useRef(0);

  useEffect(() => {
    onScanRef.current = onScan;
  }, [onScan]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  useEffect(() => {
    let cancelled = false;

    async function startCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
        const message =
          "La caméra n'est pas disponible dans ce navigateur.";

        setCameraError(message);
        onErrorRef.current?.(message);
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });

        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }

        streamRef.current = stream;

        const video = videoRef.current;
        if (!video) {
          stream.getTracks().forEach((track) => track.stop());
          streamRef.current = null;
          return;
        }

        video.srcObject = stream;
        await video.play();

        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d", {
          willReadFrequently: true,
        });

        if (!context) {
          throw new Error("Canvas 2D non disponible.");
        }

        const reader = new BrowserQRCodeReader(
          new Map([[DecodeHintType.TRY_HARDER, true]])
        );

        let decoding = false;
        let lastAttempt = 0;

        function scanFrame() {
          if (cancelled || scannedRef.current) return;

          frameRef.current = requestAnimationFrame(scanFrame);

          if (
            !video.videoWidth ||
            !video.videoHeight ||
            decoding
          ) {
            return;
          }

          const now = performance.now();
          if (now - lastAttempt < 150) return;
          lastAttempt = now;

          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;

          context.drawImage(video, 0, 0, canvas.width, canvas.height);

          decoding = true;

          let settled = false;
          const finishAttempt = (errName) => {
            if (settled) return;
            settled = true;

            decoding = false;
            attemptsRef.current += 1;
            if (errName) {
              lastErrorRef.current = errName;
            }

            const nowUi = performance.now();
            if (
              debugEnabled &&
              nowUi - lastUiUpdateRef.current > 1000
            ) {
              lastUiUpdateRef.current = nowUi;
              setDebugStats({
                attempts: attemptsRef.current,
                lastError: lastErrorRef.current,
              });
            }
          };

          const handleResult = (result) => {
            if (result && !scannedRef.current) {
              scannedRef.current = true;
              onScanRef.current?.(result.getText());
            }
          };

          try {
            const out = reader.decodeFromCanvas(canvas);
            if (out && typeof out.then === "function") {
              out
                .then(handleResult)
                .catch((err) => finishAttempt(err?.name || String(err)))
                .finally(() => finishAttempt(""));
            } else {
              handleResult(out);
              finishAttempt("");
            }
          } catch (err) {
            finishAttempt(err?.name || String(err));
          }
        }

        frameRef.current = requestAnimationFrame(scanFrame);
      } catch (error) {
        streamRef.current?.getTracks().forEach((track) => track.stop());
        streamRef.current = null;

        const message =
          error?.name === "NotAllowedError"
            ? "Accès à la caméra refusé."
            : "Impossible d'accéder à la caméra.";

        setCameraError(message);
        onErrorRef.current?.(message);
      }
    }

    startCamera();

    return () => {
      cancelled = true;

      if (frameRef.current) {
        cancelAnimationFrame(frameRef.current);
      }

      streamRef.current?.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    };
  }, [debugEnabled]);

  return (
    <div className="qr-scanner">
      <div className="qr-scanner-frame">
        <video ref={videoRef} playsInline muted autoPlay />

        {cameraError && (
          <p className="qr-scanner-error">{cameraError}</p>
        )}

        {debugEnabled && !cameraError && (
          <p className="qr-scanner-debug">
            DEBUG · {debugStats.attempts} tentatives
            {debugStats.lastError
              ? ` · dernière erreur : ${debugStats.lastError}`
              : ""}
          </p>
        )}
      </div>

      <div className="qr-scanner-actions">
        <button
          type="button"
          className="verification-button verification-button-secondary"
          onClick={onClose}
        >
          Arrêter le scan
        </button>
      </div>
    </div>
  );
}
