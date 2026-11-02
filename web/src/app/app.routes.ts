import { Routes } from '@angular/router';
import { PublicLayout } from './layouts/public-layout';
import { workspaceGuard } from './core/workspace.guard';
const info = () => import('./features/public/info').then((m) => m.Info);
export const routes: Routes = [
  {
    path: '',
    component: PublicLayout,
    children: [
      {
        path: '',
        loadComponent: () => import('./features/public/home').then((m) => m.Home),
        title: 'KeepYourID — Votre identité, votre contrôle',
      },
      {
        path: 'login',
        loadComponent: () => import('./features/authentication/login').then((m) => m.Login),
        title: 'Accès — KeepYourID',
      },
      {
        path: 'register',
        loadComponent: () => import('./features/organizations/register').then((m) => m.Register),
        title: 'Inscrire une organisation — KeepYourID',
      },
      ...[
        {
          path: 'about',
          label: 'À PROPOS',
          title: 'Une identité qui vous appartient.',
          description:
            'KeepYourID explore une infrastructure ouverte pour les identités décentralisées et les justificatifs vérifiables.',
          items: [
            {
              title: 'Notre mission',
              text: 'Permettre de prouver une information sans dépendre systématiquement de son émetteur.',
            },
            {
              title: 'Notre approche',
              text: 'Un backend modulaire, des preuves cryptographiques et un moteur de vérification indépendant.',
            },
            {
              title: 'Un projet en construction',
              text: 'Les premiers parcours d’émission sont implémentés. Le wallet et la vérification indépendante restent à développer.',
            },
          ],
        },
        {
          path: 'how-it-works',
          label: 'FONCTIONNEMENT',
          title: 'Trois acteurs. Une chaîne de confiance.',
          description:
            'De l’organisation au titulaire, puis au vérificateur : chaque acteur garde sa responsabilité.',
          items: [
            {
              title: '01 — Émettre',
              text: 'Une organisation active disposant d’un DID vérifié prépare une attestation. Une signature externe est ensuite contrôlée par le backend.',
            },
            {
              title: '02 — Conserver',
              text: 'Le futur wallet mobile permettra au titulaire de conserver ses justificatifs et de consentir à leur présentation.',
            },
            {
              title: '03 — Vérifier',
              text: 'Le moteur prévu vérifiera les preuves, les dates, le statut et la politique de confiance du vérificateur.',
            },
          ],
        },
        {
          path: 'organizations',
          label: 'ORGANISATIONS',
          title: 'Donnez une nouvelle portée à vos attestations.',
          description:
            'Universités, entreprises et institutions : préparez des justificatifs numériques dont l’origine peut être vérifiée.',
          items: [
            {
              title: 'Une identité propre',
              text: 'Associez votre organisation à un DID et démontrez le contrôle de sa clé autorisée.',
            },
            {
              title: 'Une émission maîtrisée',
              text: 'Créez un brouillon, préparez le message à signer et soumettez la signature de votre outil externe.',
            },
            {
              title: 'Un suivi clair',
              text: 'Retrouvez les justificatifs et leurs statuts dans le portail organisation.',
            },
          ],
        },
        {
          path: 'wallet',
          label: 'WALLET MOBILE',
          title: 'Vos justificatifs, à portée de main.',
          description:
            'Le portefeuille citoyen sera une application mobile distincte, développée avec Expo et React Native.',
          items: [
            {
              title: 'Conserver',
              text: 'Le stockage personnel des justificatifs est prévu dans le wallet mobile.',
            },
            {
              title: 'Présenter',
              text: 'Le titulaire devra consentir avant de partager des informations avec un service tiers.',
            },
            {
              title: 'Protéger',
              text: 'La sauvegarde, la récupération et la gestion des clés seront définies pour le wallet. Ce site ne stocke aucune clé privée.',
            },
          ],
        },
        {
          path: 'verification',
          label: 'VÉRIFICATION',
          title: 'Une preuve, plusieurs contrôles.',
          description:
            'Une signature valide et un émetteur reconnu répondent à deux questions différentes.',
          items: [
            {
              title: 'Authenticité',
              text: 'Vérifier que la signature correspond à une clé autorisée de l’émetteur.',
            },
            {
              title: 'Validité et statut',
              text: 'Contrôler les dates et le statut de révocation. Le moteur complet reste à intégrer.',
            },
            {
              title: 'Confiance',
              text: 'Appliquer la politique du vérificateur : une preuve cryptographique ne garantit pas à elle seule la légitimité de son émetteur.',
            },
          ],
        },
        {
          path: 'standards',
          label: 'CONFIANCE & STANDARDS',
          title: 'Des fondations ouvertes. Une confiance explicite.',
          description:
            'Une architecture conçue autour de standards publics et de responsabilités séparées.',
          items: [
            {
              title: 'W3C VC & DID',
              text: 'Le projet cible le modèle W3C Verifiable Credentials 2.0 et utilise des identifiants did:ethr:sepolia.',
            },
            {
              title: 'Signatures hors chaîne',
              text: 'Le backend prépare et vérifie des credentials au format JWS compact. Les données personnelles restent hors chaîne.',
            },
            {
              title: 'Ethereum Sepolia',
              text: 'Le dépôt inclut un contrat IssuerRegistry. La présence du code ne signifie pas qu’un déploiement est opérationnel.',
            },
          ],
        },
        {
          path: 'contact',
          label: 'CONTACT',
          title: 'Construisons un écosystème utile.',
          description:
            'Vous souhaitez explorer KeepYourID avec votre organisation ? Commencez par son inscription.',
          items: [
            {
              title: 'Organisations',
              text: 'Le formulaire d’inscription transmet les informations à l’API KeepYourID.',
            },
            {
              title: 'Intégration',
              text: 'Les contrats d’API et les limites actuelles sont documentés dans le dépôt du projet.',
            },
            {
              title: 'Disponibilité',
              text: 'Aucun canal de support public n’est encore configuré. Le projet reste en développement.',
            },
          ],
        },
      ].map((page) => ({
        path: page.path,
        loadComponent: info,
        title: page.label + ' — KeepYourID',
        data: page,
      })),
    ],
  },
  {
    path: '',
    canActivate: [workspaceGuard],
    loadComponent: () => import('./layouts/workspace-layout').then((m) => m.WorkspaceLayout),
    children: [
      {
        path: 'issuer/dashboard',
        loadComponent: () =>
          import('./features/credentials/credential-list').then((m) => m.CredentialList),
        title: 'Vue d’ensemble — KeepYourID',
      },
      {
        path: 'issuer/credentials',
        loadComponent: () =>
          import('./features/credentials/credential-list').then((m) => m.CredentialList),
        title: 'Justificatifs — KeepYourID',
      },
      {
        path: 'issuer/issue',
        loadComponent: () =>
          import('./features/credentials/credential-create').then((m) => m.CredentialCreate),
        title: 'Créer une attestation — KeepYourID',
      },
      {
        path: 'issuer/did',
        loadComponent: () => import('./features/did/did').then((m) => m.Did),
        title: 'Identité décentralisée — KeepYourID',
      },
      {
        path: 'issuer/credentials/:id',
        loadComponent: () =>
          import('./features/credentials/credential-detail').then((m) => m.CredentialDetail),
        title: 'Détail du justificatif — KeepYourID',
      },
      {
        path: 'verifier',
        loadComponent: () =>
          import('./features/verification/verification').then((m) => m.Verification),
        title: 'Vérification — KeepYourID',
      },
      {
        path: 'admin',
        loadComponent: () => import('./features/administration/system').then((m) => m.System),
        title: 'État des services — KeepYourID',
      },
    ],
  },
  {
    path: '**',
    component: PublicLayout,
    children: [
      {
        path: '',
        loadComponent: info,
        title: 'Page introuvable — KeepYourID',
        data: {
          label: '404',
          title: 'Cette page est introuvable.',
          description: 'Utilisez le menu pour retrouver votre chemin.',
          items: [],
        },
      },
    ],
  },
];
