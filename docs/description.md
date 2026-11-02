# KEEPYOURID
## Cahier des charges fonctionnel et technique — Frontend Web

**Version :** 1.0  
**Projet :** KeepYourID  
**Frontend :** Angular  
**Backend :** FastAPI / Python  
**Base de données :** PostgreSQL  
**Blockchain :** Solidity / Ethereum  
**Application mobile Wallet :** Expo / React Native — hors périmètre de ce document.

---

# 1. Présentation du projet

## 1.1. Contexte

KeepYourID est une plateforme d'identité numérique décentralisée permettant aux organisations d'émettre des justificatifs numériques vérifiables, aux citoyens de les conserver et aux tiers de les vérifier de manière indépendante.

La plateforme repose notamment sur :
- Les Decentralized Identifiers (DID).
- Les Verifiable Credentials (VC).
- Les signatures cryptographiques.
- Les standards W3C.
- Une infrastructure blockchain pour le registre des émetteurs.
- Un moteur autonome de vérification.

KeepYourID distingue trois acteurs principaux :

**Issuer — Émetteur**

Une organisation (université, entreprise, institution, etc.) qui émet des justificatifs numériques à destination de ses bénéficiaires.

**Holder — Détenteur**

Un citoyen qui reçoit, conserve et présente ses justificatifs numériques. Son application Wallet sera développée séparément avec Expo.

**Verifier — Vérificateur**

Une organisation ou un service qui reçoit une présentation et vérifie indépendamment l'authenticité et le statut du credential.

## 1.2. Objectif du frontend

Le frontend Web doit fournir :
1. Un site public permettant de comprendre le projet et ses fonctionnalités.
2. Un espace de gestion destiné aux organisations émettrices.
3. Un espace destiné aux vérificateurs.
4. Une interface d'administration de la plateforme, selon les fonctionnalités disponibles côté backend.

Le frontend est un client de l'API FastAPI. Il ne doit pas implémenter lui-même les règles métier, la cryptographie ou les mécanismes de confiance.

---

# 2. Périmètre du développement

## 2.1. Applications à développer

| Application | Technologie | Périmètre |
|---|---|---|
| Site public | Angular | Inclus |
| Organization Portal | Angular | Inclus |
| Verification Portal | Angular | Inclus |
| Administration | Angular | À développer progressivement |
| Identity Wallet | Expo / React Native | Exclu |

Le projet Angular doit être développé directement dans le répertoire `web/` du dépôt KeepYourID.

## 2.2. Hors périmètre

Les éléments suivants ne doivent pas être développés dans ce frontend :

- Application mobile Wallet.
- Génération et signature cryptographique des credentials.
- Génération ou gestion des clés privées des organisations.
- Implémentation du moteur de vérification.
- Déploiement et gestion directe des smart contracts.
- Gestion directe des transactions blockchain.
- Logique de révocation côté blockchain.

Ces responsabilités appartiennent au backend, au moteur de vérification ou à l'application mobile.

---

# 3. Identité visuelle et expérience utilisateur

## 3.1. Référence visuelle

Référence principale : https://walt.id/

L'accueil de Walt.id constitue une inspiration importante pour la présentation de KeepYourID.

Il faut notamment s'inspirer de :
- La qualité de la section Hero.
- La hiérarchisation des informations.
- La présentation des fonctionnalités sous forme de blocs visuels.
- La présentation des trois grands rôles de l'écosystème.
- La manière de présenter les standards et les technologies.
- La cohérence entre les pages publiques et les pages produits.

Il ne s'agit pas de reproduire Walt.id ou de copier son interface. KeepYourID doit avoir sa propre identité visuelle.

## 3.2. Direction artistique

L'interface doit transmettre :

- Confiance.
- Sécurité.
- Modernité.
- Simplicité.
- Professionnalisme.
- Transparence.

Éviter une interface trop chargée, les tableaux partout et les dashboards génériques sans personnalité.

Privilégier :
- Une typographie moderne et lisible.
- Des espaces généreux.
- Une hiérarchie visuelle claire.
- Des cartes fonctionnelles.
- Des illustrations pertinentes.
- Des transitions discrètes.
- Des tableaux lisibles.
- Des états visuels explicites.

## 3.3. Responsive design

L'interface doit fonctionner sur :
- Desktop.
- Tablette.
- Mobile.

Les interfaces de gestion peuvent privilégier le desktop, mais ne doivent pas devenir inutilisables sur mobile.

## 3.4. Cohérence des composants

Créer un système de composants réutilisables :

- Boutons.
- Inputs.
- Selects.
- Modales.
- Notifications.
- Badges de statut.
- Tableaux.
- Pagination.
- Breadcrumbs.
- Menus.
- Cartes statistiques.
- Indicateurs de chargement.
- États vides.
- Messages d'erreur.

Les différents espaces doivent partager un même langage visuel.

---

# 4. Architecture frontend

## 4.1. Organisation générale

Le frontend doit être organisé de manière modulaire.

Structure indicative :

```text
web/
├── src/
│   ├── app/
│   │   ├── core/
│   │   │   ├── auth/
│   │   │   ├── guards/
│   │   │   ├── interceptors/
│   │   │   ├── services/
│   │   │   └── config/
│   │   │
│   │   ├── shared/
│   │   │   ├── components/
│   │   │   ├── directives/
│   │   │   ├── pipes/
│   │   │   └── models/
│   │   │
│   │   ├── layouts/
│   │   │   ├── public-layout/
│   │   │   ├── issuer-layout/
│   │   │   ├── verifier-layout/
│   │   │   └── admin-layout/
│   │   │
│   │   ├── features/
│   │   │   ├── public/
│   │   │   ├── authentication/
│   │   │   ├── organizations/
│   │   │   ├── credentials/
│   │   │   ├── did/
│   │   │   ├── verification/
│   │   │   └── administration/
│   │   │
│   │   ├── app.config.ts
│   │   └── app.routes.ts
│   │
│   ├── assets/
│   ├── environments/
│   └── styles/
│
├── angular.json
├── package.json
└── README.md
```

Cette structure est indicative. Le développeur peut l'adapter aux conventions de la version d'Angular choisie, sans mélanger les responsabilités fonctionnelles.

## 4.2. Principes d'architecture

- Utiliser Angular Router pour la navigation.
- Utiliser des services pour les communications HTTP.
- Centraliser la configuration de l'API.
- Centraliser les modèles et types partagés.
- Utiliser des guards pour protéger les routes.
- Utiliser des interceptors pour les mécanismes transversaux HTTP.
- Séparer les composants de présentation des services d'accès aux données.
- Éviter les composants géants.
- Éviter de dupliquer les appels API.
- Ne jamais mettre de secrets ou de clés privées dans le frontend.

Le choix des bibliothèques complémentaires doit rester raisonnable. Éviter d'ajouter des dépendances simplement pour résoudre des problèmes que le framework gère déjà.

---

# 5. Site public

Préfixe : aucun.

Le site public est la vitrine de KeepYourID. Il doit permettre à un visiteur de comprendre rapidement le fonctionnement de la plateforme et les possibilités offertes.

## 5.1. Accueil — `/`

**Priorité : très élevée**

La page d'accueil doit être la page la plus travaillée visuellement.

### Section 1 — Hero

Présenter clairement KeepYourID.

Proposition de message :

**Your identity. Your credentials. Your control.**

Sous-titre :

"Une infrastructure d'identité numérique permettant d'émettre, de conserver et de vérifier des justificatifs numériques de manière sécurisée et indépendante."

Actions :
- Découvrir la plateforme.
- Accéder à la plateforme.
- Découvrir les solutions pour les organisations.

Ajouter une illustration ou une représentation visuelle de l'écosystème.

### Section 2 — Présentation du problème

Expliquer les limites des justificatifs traditionnels :

- Difficulté de vérifier l'authenticité.
- Dépendance à l'organisme émetteur pour chaque vérification.
- Risques de falsification.
- Difficultés de partage et de contrôle des données.

### Section 3 — Fonctionnement de KeepYourID

Présenter les trois acteurs :

**Issue**

Les organisations créent et émettent des credentials numériques.

**Hold**

Les citoyens conservent leurs credentials dans leur portefeuille numérique.

**Verify**

Les vérificateurs contrôlent indépendamment les justificatifs présentés.

### Section 4 — Fonctionnalités

Présenter :
- Émission de credentials.
- Identifiants décentralisés.
- Portefeuille numérique.
- Vérification cryptographique.
- Gestion du statut des credentials.
- Registre des émetteurs.

### Section 5 — Architecture de confiance

Expliquer les principes :
- Signature cryptographique.
- DID et DID Documents.
- Vérification indépendante.
- Registre blockchain.
- Politiques de confiance.

Ne pas présenter la blockchain comme une garantie automatique de légitimité juridique.

### Section 6 — Standards

Présenter les standards et technologies supportés, notamment :
- W3C Verifiable Credentials Data Model 2.0.
- Decentralized Identifiers.
- VC-JWT.
- Cryptographie à clé publique.

Ne pas annoncer une compatibilité avec un standard ou un format qui n'est pas réellement implémenté.

### Section 7 — Cas d'utilisation

Exemples :
- Diplômes universitaires.
- Certificats professionnels.
- Attestations.
- Justificatifs institutionnels.

### Section 8 — Appel à l'action

Inviter les organisations à rejoindre la plateforme et les visiteurs à découvrir son fonctionnement.

### Section 9 — Footer

Liens vers :
- À propos.
- Documentation.
- Organisations.
- Wallet.
- Vérification.
- Contact.
- Conditions d'utilisation.
- Politique de confidentialité.

## 5.2. À propos — `/about`

Présenter :
- La vision de KeepYourID.
- Sa mission.
- Les problèmes auxquels le projet répond.
- Les principes de conception.
- L'indépendance de la vérification.

## 5.3. Fonctionnement — `/how-it-works`

Présenter un parcours complet :

1. Une organisation s'inscrit.
2. Elle configure son identité décentralisée.
3. Elle prépare un credential.
4. Elle émet le credential.
5. Le citoyen le reçoit dans son Wallet.
6. Le citoyen présente son credential à un vérificateur.
7. Le vérificateur contrôle la signature, le statut et la politique de confiance.

Utiliser des schémas ou illustrations pour rendre le processus compréhensible.

## 5.4. Organisations — `/organizations`

Présenter les avantages de la plateforme pour les organisations :
- Émission de credentials.
- Gestion de leurs bénéficiaires.
- Identité décentralisée.
- Gestion des credentials émis.
- Historique des opérations.

CTA : créer un compte organisation.

## 5.5. Wallet — `/wallet`

Présenter le fonctionnement du portefeuille numérique.

Cette page est informative. Elle ne doit pas tenter de remplacer l'application mobile Expo.

## 5.6. Vérification — `/verification`

Présenter :
- La vérification indépendante.
- Le contrôle des signatures.
- Le contrôle du statut.
- La résolution du DID de l'émetteur.
- L'application d'une politique de confiance.

## 5.7. Trust — `/trust`

Expliquer :
- Le registre des émetteurs.
- La différence entre enregistrement et reconnaissance.
- La différence entre validité cryptographique et confiance institutionnelle.
- Le fonctionnement des statuts ACTIVE et SUSPENDED.

## 5.8. Standards — `/standards`

Présenter les standards réellement supportés par KeepYourID.

## 5.9. Documentation — `/documentation`

Prévoir une page de présentation de la documentation technique et des ressources développeurs.

## 5.10. Contact — `/contact`

Formulaire de contact, sous réserve de disposer d'un endpoint backend correspondant.

---

# 6. Authentification et onboarding

Routes principales :

```text
/login
/register/organization
/forgot-password
/reset-password
/verify-email
```

## 6.1. Connexion

Champs :
- Adresse e-mail.
- Mot de passe.

Comportements :
- Validation des champs.
- Affichage des erreurs.
- Indicateur de chargement.
- Gestion des erreurs d'authentification.
- Redirection selon les permissions et le rôle.

## 6.2. Inscription d'une organisation

Champs à adapter au schéma réel du backend :
- Nom de l'organisation.
- Adresse e-mail.
- Mot de passe.
- Confirmation du mot de passe.
- Informations de contact éventuellement disponibles.

L'inscription ne doit pas afficher un statut d'approbation administrative obligatoire.

Une organisation qui s'inscrit devient ACTIVE selon les règles métier définies.

## 6.3. Gestion de session

Le frontend doit :
- Gérer les tokens conformément au mécanisme d'authentification backend.
- Gérer les sessions expirées.
- Empêcher l'accès aux routes protégées.
- Gérer les erreurs 401 et 403.
- Ne pas stocker les clés privées DID ou blockchain.

Le mécanisme de stockage des tokens doit être défini avec le développeur backend avant l'intégration finale.

---

# 7. Organization Portal — Espace émetteur

Préfixe :

```text
/organization
```

Cet espace est destiné aux organisations qui émettent des credentials.

## 7.1. Dashboard — `/organization/dashboard`

Afficher :
- Nombre de credentials émis.
- Nombre de credentials actifs.
- Nombre de credentials révoqués, si disponible.
- Nombre de bénéficiaires, si disponible.
- Dernières opérations.
- Statut de l'organisation.
- État du DID.

Les statistiques doivent provenir de l'API. Ne pas inventer des valeurs.

## 7.2. Profil de l'organisation — `/organization/profile`

Afficher et permettre de modifier les informations autorisées :
- Nom.
- Adresse e-mail.
- Description.
- Informations de contact.
- Informations institutionnelles.

Respecter les champs et permissions du backend.

## 7.3. Équipe — `/organization/team`

Fonctionnalités :
- Liste des membres.
- Consultation des rôles.
- Invitation ou ajout de membres si l'API le permet.
- Modification des rôles autorisés.
- Retrait d'un membre selon les permissions.

Prévoir des états vides et des confirmations avant les opérations sensibles.

## 7.4. Identité décentralisée — `/organization/did`

Afficher :
- DID de l'organisation.
- Méthode DID.
- Réseau utilisé.
- État du contrôle de la clé.
- Date de création ou d'enregistrement, si disponible.

L'interface doit distinguer clairement :

**DID enregistré** : un identifiant est associé à l'organisation.

**Contrôle du DID vérifié** : l'organisation a démontré le contrôle de la clé correspondante.

Cela ne constitue pas automatiquement une reconnaissance juridique de l'organisation.

## 7.5. Liste des credentials — `/organization/credentials`

Afficher un tableau comprenant :
- Identifiant.
- Type.
- Bénéficiaire.
- Date de création.
- Statut.
- Actions disponibles.

Filtres :
- Type.
- Statut.
- Date.
- Recherche.

Prévoir :
- Pagination.
- Chargement.
- Liste vide.
- Erreurs API.

## 7.6. Création d'un credential — `/organization/credentials/create`

Prévoir un formulaire structuré.

Étapes :

**Étape 1 — Type**

Choisir le type de credential.

**Étape 2 — Bénéficiaire**

Saisir les informations du détenteur selon le schéma autorisé.

**Étape 3 — Données**

Renseigner les informations propres au credential.

**Étape 4 — Révision**

Afficher un résumé des informations avant émission.

**Étape 5 — Préparation**

Envoyer les informations au backend pour préparer l'émission.

**Étape 6 — Finalisation**

Afficher le résultat de l'émission après confirmation du backend.

Ne jamais signer directement le credential dans Angular.

## 7.7. Détails d'un credential — `/organization/credentials/:id`

Afficher :
- Identifiant.
- Type.
- Bénéficiaire.
- Émetteur.
- Date d'émission.
- Statut.
- Informations disponibles.
- Informations techniques non sensibles.

## 7.8. Gestion du statut

Prévoir une interface pour consulter le statut du credential et déclencher les opérations de révocation lorsque l'API correspondante sera disponible.

Ne pas confondre suspension d'un émetteur et révocation d'un credential.

## 7.9. Activité — `/organization/activity`

Historique des opérations :
- Création.
- Préparation d'émission.
- Émission.
- Modification.
- Révocation, si disponible.

## 7.10. Paramètres — `/organization/settings`

Prévoir les paramètres accessibles à l'organisation.

---

# 8. Verification Portal — Espace vérificateur

Préfixe :

```text
/verifier
```

Cet espace permet aux services tiers de vérifier des credentials.

## 8.1. Dashboard — `/verifier/dashboard`

Afficher :
- Nombre de vérifications.
- Vérifications réussies.
- Vérifications échouées.
- Dernières vérifications.

Toutes les statistiques doivent provenir du backend.

## 8.2. Vérification — `/verifier/verify`

Prévoir une interface permettant de soumettre un credential ou une présentation selon le format accepté par le moteur de vérification.

Ne pas supposer que le backend accepte n'importe quel document PDF ou image comme preuve vérifiable.

## 8.3. Scan — `/verifier/scan`

Prévoir une interface de lecture QR code lorsque le protocole de présentation correspondant sera défini.

Le QR code ne doit pas être considéré comme une preuve cryptographique à lui seul.

## 8.4. Résultat — `/verifier/result/:id`

Afficher un résultat structuré :

| Contrôle | Résultat |
|---|---|
| Format | Valide / Invalide |
| Signature | Valide / Invalide |
| Émetteur DID | Résolu / Non résolu |
| Statut | Actif / Révoqué / Inconnu |
| Politique de confiance | Accepté / Refusé / Non déterminé |

Prévoir un état d'erreur distinct lorsque la vérification ne peut pas être effectuée.

Ne pas afficher simplement un gros badge « VALIDE » sans expliquer ce qui a été contrôlé.

La validité cryptographique et la reconnaissance de l'émetteur sont deux dimensions différentes.

## 8.5. Historique — `/verifier/history`

Afficher :
- Date.
- Type de credential.
- Résultat.
- Identifiant de vérification.

Respecter les restrictions de confidentialité : ne pas exposer inutilement les données personnelles des détenteurs.

## 8.6. Émetteurs de confiance — `/verifier/trusted-issuers`

Prévoir une interface pour consulter les émetteurs reconnus selon les politiques du vérificateur.

La gestion complète des politiques pourra être ajoutée lorsque le backend l'exposera.

## 8.7. Paramètres — `/verifier/settings`

Prévoir les paramètres du compte et de l'espace vérificateur.

---

# 9. Administration de la plateforme

Préfixe :

```text
/admin
```

Cette interface est destinée aux administrateurs autorisés de KeepYourID.

Elle sera développée progressivement, en fonction des endpoints disponibles.

Pages prévues :

| Route | Fonction |
|---|---|
| `/admin/dashboard` | Vue globale |
| `/admin/organizations` | Liste des organisations |
| `/admin/organizations/:id` | Détails d'une organisation |
| `/admin/issuers` | Registre des émetteurs |
| `/admin/registrars` | Gestion des registrars autorisés |
| `/admin/blockchain` | Informations sur le réseau et le contrat |
| `/admin/transactions` | Historique des transactions |
| `/admin/audit-logs` | Journaux d'audit |
| `/admin/users` | Gestion des comptes |
| `/admin/system` | État des services |

### Règles importantes

- Ne pas permettre d'opérations administratives sans endpoint et permission correspondants.
- Les actions sensibles doivent demander confirmation.
- Les opérations blockchain doivent être déclenchées par le backend.
- Ne jamais exposer la clé privée du registrar.
- Ne pas confondre les droits d'administration et les droits de registrar.

---

# 10. API et intégration backend

## 10.1. Principe général

FastAPI constitue la source de vérité métier.

Angular doit consommer les endpoints documentés par le backend.

La documentation OpenAPI sera la référence contractuelle pour :
- Les routes.
- Les méthodes HTTP.
- Les paramètres.
- Les schémas de requête.
- Les schémas de réponse.
- Les erreurs.

Documentation locale attendue :

```text
http://localhost:<BACKEND_PORT>/docs
```

L'URL réelle dépend de la configuration du backend.

## 10.2. Credentials

Les routes d'émission déjà établies sont organisées autour de l'organisation :

```text
POST /api/v1/organizations/{organization_id}/credentials

GET /api/v1/organizations/{organization_id}/credentials

GET /api/v1/organizations/{organization_id}/credentials/{credential_id}

POST /api/v1/organizations/{organization_id}/credentials/{credential_id}/prepare-issuance

POST /api/v1/organizations/{organization_id}/credentials/{credential_id}/complete-issuance
```

Le frontend doit respecter ces routes et leurs schémas réels.

Ne pas inventer d'autres routes pour contourner les contrôles d'accès.

## 10.3. Gestion des erreurs HTTP

Prévoir un mécanisme commun de traitement :

| Code | Comportement attendu |
|---|---|
| 400 | Requête incorrecte |
| 401 | Session absente ou expirée |
| 403 | Permission insuffisante |
| 404 | Ressource inexistante |
| 409 | Conflit métier |
| 422 | Erreur de validation |
| 429 | Trop de requêtes |
| 500 | Erreur interne |
| 503 | Service temporairement indisponible |

Afficher des messages compréhensibles, sans exposer les détails internes ou les traces techniques du backend.

## 10.4. Environnements

Prévoir une configuration distincte :

- Développement local.
- Staging.
- Production.

L'URL de l'API doit être configurable sans modifier les composants Angular.

---

# 11. Sécurité frontend

La sécurité est particulièrement importante compte tenu de la nature du projet.

Exigences :

1. Protéger toutes les routes privées.
2. Vérifier les permissions côté backend, même si Angular masque les boutons.
3. Ne jamais considérer un guard Angular comme une protection métier.
4. Ne jamais stocker de clé privée dans le frontend.
5. Ne jamais intégrer de secrets dans le code compilé.
6. Utiliser HTTPS en production.
7. Éviter les données personnelles dans les logs du navigateur.
8. Éviter les informations sensibles dans les URL.
9. Gérer les expirations de session.
10. Respecter les règles de sécurité contre les attaques XSS et CSRF selon le mécanisme d'authentification retenu.

Le frontend ne doit jamais être la seule couche de contrôle des permissions.

---

# 12. Tests et qualité

Prévoir :

## Tests unitaires

- Services API.
- Guards.
- Interceptors.
- Composants importants.
- Validations de formulaires.

## Tests d'intégration

- Connexion.
- Inscription organisation.
- Chargement du dashboard.
- Création d'un credential.
- Préparation et finalisation d'émission.
- Affichage des résultats de vérification.

## Tests fonctionnels

- Parcours d'une organisation.
- Parcours d'un vérificateur.
- Gestion des erreurs API.
- Gestion des permissions.
- Navigation entre les espaces.

Le projet doit pouvoir être construit et exécuté sans erreurs bloquantes.

---

# 13. Découpage du développement

Le développement doit être progressif.

## Phase 1 — Fondations

- Initialisation Angular dans `web/`.
- Configuration des environnements.
- Architecture des dossiers.
- Routing.
- Design system.
- Layout public.
- Layouts privés.
- Client API.
- Gestion initiale de l'authentification.

Livrable : une application Angular structurée et navigable.

## Phase 2 — Site public

- Accueil.
- À propos.
- Fonctionnement.
- Organisations.
- Wallet.
- Vérification.
- Standards.
- Contact.

Livrable : site public cohérent et responsive.

## Phase 3 — Organization Portal

- Dashboard.
- Profil.
- DID.
- Credentials.
- Création.
- Préparation d'émission.
- Finalisation.
- Historique.

Livrable : parcours complet d'émission connecté au backend.

## Phase 4 — Verification Portal

- Dashboard.
- Soumission.
- Scan selon disponibilité du protocole.
- Résultat.
- Historique.

Livrable : parcours de vérification connecté au moteur de vérification.

## Phase 5 — Administration

- Organisations.
- Émetteurs.
- Registrars.
- Blockchain.
- Transactions.
- Audit.

Livrable : interface d'administration des fonctionnalités effectivement exposées.

---

# 14. Critères d'acceptation

Le frontend sera considéré comme intégrable lorsque :

- [ ] Le projet se trouve dans `web/`.
- [ ] Le projet Angular démarre localement.
- [ ] La navigation entre les espaces fonctionne.
- [ ] Le site public est responsive.
- [ ] Les espaces privés sont protégés.
- [ ] Les appels API utilisent les services centralisés.
- [ ] Les erreurs API sont correctement gérées.
- [ ] Les formulaires disposent de validations.
- [ ] Les données affichées proviennent du backend.
- [ ] Le workflow d'émission respecte les endpoints existants.
- [ ] Les résultats de vérification distinguent les contrôles effectués.
- [ ] Aucun secret ou clé privée n'est exposé.
- [ ] Les tests principaux passent.
- [ ] Le build de production fonctionne.
- [ ] Un README explique l'installation et l'exécution.

---

# 15. Livrables attendus

Le développeur frontend doit fournir :

1. Le code source Angular dans `web/`.
2. Une architecture organisée et documentée.
3. Les pages publiques.
4. Les espaces Issuer et Verifier.
5. Les composants partagés.
6. Les services d'intégration API.
7. Les mécanismes de navigation et de protection des routes.
8. Les tests.
9. Un fichier `.env.example` ou une configuration équivalente, sans secrets.
10. Un README avec les commandes d'installation, de lancement et de build.
11. Une liste des endpoints utilisés.
12. Une liste des fonctionnalités bloquées par l'absence d'API backend.

---

# 16. Organisation du travail et collaboration

Le développement se déroule dans le dépôt Git principal de KeepYourID.

Le frontend doit rester isolé dans :

```text
keepyourid/web/
```

Le développeur frontend travaille sur ses branches et soumet ses modifications pour intégration.

Les changements backend restent sous la responsabilité du développeur backend.

Les contrats API doivent être discutés avant toute modification incompatible.

En cas d'endpoint manquant :
1. Identifier précisément la fonctionnalité concernée.
2. Décrire les données nécessaires.
3. Proposer le contrat HTTP attendu.
4. Faire valider ce contrat par le responsable backend.
5. Utiliser des données fictives uniquement pour les maquettes, jamais pour simuler une fonctionnalité réellement opérationnelle.

---

# 17. Priorité immédiate

Le premier objectif n'est pas de développer toutes les pages en même temps.

Le développeur doit commencer par :

1. Initialiser Angular dans `web/`.
2. Construire le système de navigation et les layouts.
3. Définir les composants visuels communs.
4. Développer la page d'accueil en s'inspirant de la qualité visuelle de Walt.id.
5. Développer le parcours de connexion.
6. Commencer l'Organization Portal en s'appuyant sur les endpoints Credentials existants.

Le Verification Portal viendra ensuite, en fonction de l'état d'avancement du moteur de vérification.

**Objectif final :** obtenir une interface Web professionnelle, cohérente, maintenable et réellement connectée à KeepYourID, sans dupliquer les responsabilités du backend.

---

**Responsable frontend :** Développeur Angular  
**Responsable backend et intégration :** Développeur FastAPI  
**Application mobile :** Projet séparé sous Expo / React Native  
