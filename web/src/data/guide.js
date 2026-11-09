export const guideProfiles = [
  {
    id: "issuer",
    label: "Organisateur",
    tagline: "Émettez des justificatifs signés à vos clients.",
    steps: [
      {
        title: "Créer un compte & se connecter",
        description:
          "Inscrivez-vous sur la plateforme puis connectez-vous pour accéder à votre espace.",
        link: { to: "/register", label: "S'inscrire" },
      },
      {
        title: "Créer l'organisation",
        description:
          "Créez un espace organisation pour regrouper vos justificatifs et gérer vos membres.",
        link: { to: "/organizations", label: "Mes organisations" },
      },
      {
        title: "Connecter le wallet & associer le DID",
        description:
          "Depuis la page de votre organisation, liez le portefeuille MetaMask de l'organisation, puis générez et signez le challenge pour enregistrer le DID émetteur.",
        link: { to: "/organizations", label: "Espace organisation" },
      },
      {
        title: "Préparer & émettre le justificatif",
        description:
          "Créez un brouillon de credential (carte d'identité, attestation...), renseignez le DID du titulaire, signez l'émission via MetaMask et publiez-la.",
        link: { to: "/organizations", label: "Gérer les justificatifs" },
      },
      {
        title: "Suivre & révoquer",
        description:
          "Consultez le registre de vos justificatifs émis et révoquez ceux qui ne sont plus valides.",
        link: { to: "/organizations", label: "Registre" },
      },
    ],
  },
  {
    id: "holder",
    label: "Client (Titulaire)",
    tagline: "Conservez et présentez vos justificatifs.",
    steps: [
      {
        title: "Se connecter",
        description:
          "Créez un compte puis connectez-vous pour accéder à votre espace wallet.",
        link: { to: "/login", label: "Connexion" },
      },
      {
        title: "Connecter MetaMask sur Sepolia",
        description:
          "Ouvrez votre wallet et assurez-vous que MetaMask est connecté au réseau Sepolia.",
        link: { to: "/wallet", label: "Mon wallet" },
      },
      {
        title: "Associer & vérifier le DID titulaire",
        description:
          "Le système associe votre DID et vérifie votre contrôle du portefeuille via une signature de challenge.",
        link: { to: "/wallet", label: "Mon wallet" },
      },
      {
        title: "Gérer le wallet",
        description:
          "Assurez-vous que votre portefeuille est actif et prêt à recevoir des credentials.",
        link: { to: "/wallet", label: "Mon wallet" },
      },
      {
        title: "Consulter les credentials reçues",
        description:
          "Visualisez dans votre espace personnel les justificatifs émis à votre attention.",
        link: { to: "/wallet", label: "Mes justificatifs" },
      },
      {
        title: "Présenter par QR code",
        description:
          "Affichez le QR code de présentation (lien vers le signed_credential) pour qu'un vérificateur le scanne.",
        link: { to: "/wallet", label: "Présenter" },
      },
    ],
  },
  {
    id: "verifier",
    label: "Vérificateur",
    tagline: "Vérifiez un justificatif sans compte.",
    steps: [
      {
        title: "Accéder à l'espace de vérification",
        description:
          "Rendez-vous sur la page publique de vérification : aucune connexion n'est requise.",
        link: { to: "/verify", label: "Vérifier" },
      },
      {
        title: "Présenter le justificatif",
        description:
          "Scannez le QR code affiché par le client avec la caméra, ou importez le fichier JSON de l'enveloppe signée.",
        link: { to: "/verify", label: "Scanner / importer" },
      },
      {
        title: "Analyser le résultat",
        description:
          "Le moteur vérifie la signature EIP-191, le DID de l'émetteur, la non-révocation (BitstringStatusList) et l'expiration de la credential.",
        link: { to: "/verify", label: "Voir un exemple" },
      },
    ],
  },
];
