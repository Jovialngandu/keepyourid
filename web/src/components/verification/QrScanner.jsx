import { useEffect, useRef, useState } from "react";
import jsQR from "jsqr";

import "../../styles/verification.css";

export default function QrScanner({ onScan, onError, onClose }) {
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const frameRef = useRef(null);
  const scannedRef = useRef(false);

  const onScanRef = useRef(onScan);
  const onErrorRef = useRef(onError);

  const [cameraError, setCameraError] = useState("");

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

        function scanFrame() {
          if (cancelled || scannedRef.current) return;

          frameRef.current = requestAnimationFrame(scanFrame);

          if (!video.videoWidth || !video.videoHeight) return;

          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;

          context.drawImage(video, 0, 0, canvas.width, canvas.height);

          const imageData = context.getImageData(
            0,
            0,
            canvas.width,
            canvas.height
          );

          const code = jsQR(
            imageData.data,
            imageData.width,
            imageData.height
          );

          if (code?.data && !scannedRef.current) {
            scannedRef.current = true;
            onScanRef.current?.(code.data);
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
  }, []);

  return (
    <div className="qr-scanner">
      <div className="qr-scanner-frame">
        <video ref={videoRef} playsInline muted autoPlay />

        {cameraError && (
          <p className="qr-scanner-error">{cameraError}</p>
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
