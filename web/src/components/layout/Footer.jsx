function Footer() {
  return (
    <footer className="footer">
      <a href="/" className="brand">
        keepyourid<span>.</span>
      </a>

      <p>
        Infrastructure d'identité numérique et de justificatifs vérifiables.
      </p>

      <span>© {new Date().getFullYear()} KeepYourID</span>
    </footer>
  );
}

export default Footer;