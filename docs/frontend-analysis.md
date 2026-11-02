# Analyse et intégration du frontend

## Sources et arbitrages

Analyse du dépôt, de `docs/architecture.md`, de `docs/description.md` et du document `KeepYourID-documentation.md` contenu dans l’archive fournie. L’archive est une synthèse de discussion, pas une transcription complète ni un contrat d’API. Elle mentionne une archive Angular distincte qui n’a pas été fournie.

Le cahier des charges du dépôt précise davantage le périmètre : Angular dans `web/`, wallet mobile séparé, backend source de vérité. Il prime ici pour l’organisation du code. Les endpoints proposés dans la synthèse ont été comparés aux routers réels avant intégration. Aucune instruction opérationnelle contenue dans l’archive n’a été exécutée comme une commande.

## État réévalué

Le dépôt contient maintenant les organisations, l’enregistrement et la preuve de contrôle DID, les credentials, la préparation/finalisation JWS et le contrat Solidity `IssuerRegistry` avec ses tests Foundry. Le README initial sous-estime cet avancement. La présence d’un contrat ou d’un adaptateur ne prouve pas un déploiement ni une intégration réseau opérationnelle.

Le parcours d’émission repose sur une organisation active et son DID vérifié, puis un brouillon, un message de signature fourni par le backend et une signature externe validée à la finalisation. Le navigateur n’a pas à créer ou conserver de clé privée.

## Frontend réalisé

- Angular standalone, routes différées par fonctionnalité, layouts public et portail.
- Accueil et pages fonctionnement, organisations, wallet, vérification, standards, contact et à propos.
- Inscription d’organisation via l’API existante.
- Portail local : liste, recherche, filtre, pagination, création et détail des credentials.
- Préparation et finalisation d’émission avec confirmation, signature externe et export du résultat JWS.
- Enregistrement DID et challenge de preuve de contrôle avec signature externe.
- Vérification présentée comme indisponible tant qu’aucun endpoint métier ne l’expose ; aucun résultat fictif.
- Supervision limitée au healthcheck réellement disponible.
- Configuration publique à l’exécution et proxy local pour éviter de modifier le backend pour CORS.

## Dépendances backend et limites

1. Aucune API de connexion, session ou permissions : l’accès au portail est fermé par défaut. `workspaceEnabled` ouvre seulement un outil d’intégration local et ne protège aucune opération serveur. Une authentification réelle doit remplacer ce mécanisme avant ouverture aux utilisateurs.
2. `OrganizationService.register` référence encore `OrganizationStatus.PENDING`, absent de l’énumération. L’inscription peut échouer côté serveur. Aucun changement backend n’est inclus dans le travail frontend.
3. L’enregistrement d’un DID exige une organisation active, alors que la documentation décrit sa configuration avant validation : parcours à harmoniser.
4. Pas d’API de vérification VC/VP, de révocation, de présentations, d’audit, de gestion des comptes ou d’administration des registrars. Ces fonctions ne sont pas simulées.
5. Pas de GET organisation/profil ni de liste d’organisations : le portail local demande explicitement un UUID, conservé seulement en mémoire.
6. L’API de détail credential n’expose pas le JWS signé. Le téléchargement est possible immédiatement après finalisation ; un endpoint ou champ dédié serait nécessaire pour le récupérer plus tard.
7. `DID_RESOLVER_URL` est lu avec `os.getenv`, alors que `.env` est chargé dans Pydantic Settings. Sa configuration doit être vérifiée dans l’environnement du backend.
8. La divulgation sélective, le wallet et le contrôle de révocation restent des objectifs, pas des propriétés garanties du JWS actuel.

## Conventions Git

Historique KeepYourID : commits français, courts, principalement `[ADD]` et `[UPDATE]`, branches `feature/...`. L’autre dépôt consulté, `open_smr`, utilise aussi des messages français centrés sur le résultat, sans préfixe systématique. Le frontend conserve les préfixes du dépôt KeepYourID sur une branche dédiée. Aucun push ni fusion automatique.

## Validation

Les tests frontend ciblent les contrats HTTP, les erreurs sans fuite de traces serveur, la fermeture du portail, la validation JSON et le parcours de finalisation d’émission. Les mocks de test ne constituent pas une validation de l’API réelle, de PostgreSQL ou de Sepolia. Voir le README frontend pour les commandes.

Validation effectuée : build de production réussi ; 19 tests réussis sur 6 fichiers, dont navigation, rendu de l’accueil, redirection du portail et page 404. Le build nécessite de sortir du sandbox Windows pour permettre à esbuild de résoudre les dossiers parents. L’accès automatisé au navigateur est indisponible : aucune vérification visuelle desktop/mobile n’est revendiquée. Le serveur backend et Sepolia n’ont pas été testés de bout en bout.
