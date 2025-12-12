# GaragePlus - Système de Gestion de Garage Automobile

> Application web Django pour la gestion complète des réparations automobiles

[![Django](https://img.shields.io/badge/Django-6.0-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Academic-red.svg)]()

## Table des Matières

- [À propos](#à-propos)
- [Contexte](#contexte)
- [Fonctionnalités](#fonctionnalités)
- [Technologies](#technologies)
- [Architecture](#architecture)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du Projet](#structure-du-projet)
- [Modèles de Données](#modèles-de-données)
- [Sécurité](#sécurité)
- [Équipe](#équipe)

## À propos

**GaragePlus** est une application web complète développée dans le cadre du projet universitaire L3 MIAGE à l'Université Paris Nanterre (2024/2025). Ce système digitalise l'ensemble du processus de réparation automobile, de la déclaration du problème à la facturation.

### Problématique

Actuellement, la plupart des garages automobiles fonctionnent avec des méthodes traditionnelles et manuelles :
- Informations dispersées entre papier, téléphone et emails
- Calculs de devis manuels et sujets aux erreurs
- Aucune visibilité pour les clients sur l'état d'avancement
- Gestion des rendez-vous inefficace avec risques de double réservation
- Archivage difficile des documents
- Absence de traçabilité des communications

### Solution

GaragePlus propose une solution web complète qui digitalise l'ensemble du processus, offrant :
- **Transparence totale** pour les clients avec suivi en temps réel
- **Efficacité opérationnelle** pour le personnel du garage
- **Image professionnelle** et compétitivité accrue
- **Traçabilité** complète des données et conformité

## Contexte

- **Établissement :** Université Paris Nanterre - L3 MIAGE
- **Année universitaire :** 2024/2025
- **Date de soutenance :** 12/12/2025
- **Version du projet :** 3.0

## Fonctionnalités

### Pour les Clients

- **Gestion de compte**
  - Inscription et connexion sécurisée
  - Réinitialisation de mot de passe
  - Profil utilisateur avec coordonnées

- **Gestion des véhicules**
  - Ajout de véhicules (marque, modèle, année, kilométrage)
  - Modification des informations
  - Suppression logique (préservation de l'historique)
  - Suivi de l'historique complet

- **Demandes de réparation**
  - Création de dossiers de réparation
  - Sélection de pannes via interface à boutons (pas de texte libre)
  - Génération automatique de devis détaillés
  - Téléchargement des devis en PDF

- **Gestion des rendez-vous**
  - Visualisation des créneaux disponibles
  - Réservation de rendez-vous (après acceptation du devis)
  - Modification jusqu'à 24h avant
  - Annulation avec délai de prévenance

- **Suivi en temps réel**
  - Timeline de progression du dossier
  - Notifications in-app sur les changements de statut
  - Consultation des factures et historique des paiements

### Pour les Gestionnaires

- **Tableau de bord centralisé**
  - Vue d'ensemble de tous les dossiers
  - Recherche et filtres avancés
  - Indicateurs de performance

- **Gestion des devis**
  - Révision et modification avant envoi
  - Validation et verrouillage
  - Suivi des acceptations/refus

- **Workflow des dossiers**
  - Gestion des statuts (Nouveau → Devis émis → Accepté → RDV → En cours → Prêt → Clôturé)
  - Définition des délais estimés (ETA)
  - Notifications automatiques aux clients

- **Facturation**
  - Génération automatique des factures
  - Suivi des paiements
  - Numérotation séquentielle (FAC-YYYY-###)

- **Historique et traçabilité**
  - Audit trail de tous les changements
  - Historique des statuts avec horodatage

### Pour les Administrateurs

- **Configuration système**
  - Gestion des utilisateurs (clients, gestionnaires, admins)
  - Configuration du catalogue de pannes
  - Tarification (taux horaire, TVA)
  - Paramètres système (validité des devis, délais d'annulation, etc.)

- **Gestion des créneaux**
  - Définition des plages horaires récurrentes
  - Gestion des exceptions (jours fériés, fermetures)
  - Créneaux ponctuels

## Technologies

### Stack Technique

- **Framework :** Django 6.0
- **Langage :** Python 3.13+
- **Base de données :** SQLite (dev) / PostgreSQL (production)
- **Architecture :** MTV (Model-Template-View)

### Dépendances Principales

- **Génération PDF :** xhtml2pdf, ReportLab, Pillow, PyPDF
- **Traitement HTML/CSS :** html5lib, pyphen
- **Requêtes HTTP :** requests, urllib3
- **Traitement de données :** PyYAML, sqlparse
- **Gestion du temps :** tzdata, tzlocal
- **Email :** Backend Django (console pour dev, SMTP pour production)

### Sécurité

- Protection CSRF intégrée à Django
- Protection XSS (SECURE_BROWSER_XSS_FILTER)
- Protection contre le click-jacking (X-FRAME-OPTIONS: DENY)
- Timeout de session après 30 minutes d'inactivité
- Verrouillage de compte après échecs de connexion
- Mot de passe minimum 8 caractères
- Support HTTPS/SSL pour la production

## Architecture

### Architecture Modulaire (8 Applications Django)

```
garage/
├── accounts/       # Authentification et profils utilisateurs
├── vehicles/       # Gestion des véhicules
├── cases/          # Gestion des dossiers de réparation
├── catalog/        # Catalogue de pannes et tarification
├── quotes/         # Génération et gestion des devis
├── appointments/   # Planification des rendez-vous
├── billing/        # Facturation et paiements
└── notifications/  # Notifications in-app
```

### Workflow Principal

```
1. Client crée un compte
2. Ajoute son véhicule
3. Déclare un problème → Création d'un dossier
4. Sélectionne les pannes depuis le catalogue
5. Système génère automatiquement un devis détaillé
6. Client accepte ou refuse le devis
7. Client réserve un rendez-vous (si accepté)
8. Gestionnaire fait progresser le dossier (En cours → Prêt → Clôturé)
9. Client reçoit des notifications à chaque étape
10. Facture générée automatiquement à la fin
```

### Diagrammes UML

Le projet inclut plusieurs diagrammes techniques dans le dossier `cahier de charge/` :
- **Cas d'utilisation** ([Cas_utilisation.png](cahier%20de%20charge/Cas_utilisation.png))
- **Diagramme de classes UML** ([UML.png](cahier%20de%20charge/UML.png))
- **Architecture MVT** ([MVT.png](cahier%20de%20charge/MVT.png))
- **Infrastructure 3-tiers** ([Physique_Trois-Tiers.png](cahier%20de%20charge/Physique_Trois-Tiers.png))

## Installation

### Prérequis

- Python 3.13 ou supérieur
- pip (gestionnaire de paquets Python)
- Environnement virtuel (recommandé)

### Étapes d'Installation

1. **Cloner le repository**
```bash
git clone <url-du-repo>
cd projetwebl3-main
```

2. **Créer et activer un environnement virtuel**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configurer les variables d'environnement**
```bash
# Copier le fichier d'exemple
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Éditer .env avec vos paramètres
```

Variables importantes à configurer :
```env
DJANGO_ENV=development
DJANGO_SECRET_KEY=votre-clé-secrète-unique
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
GARAGE_HOURLY_RATE=60.00
GARAGE_VAT_RATE=0.20
TZ=Europe/Paris
```

5. **Appliquer les migrations**
```bash
python manage.py migrate
```

6. **Créer un superutilisateur**
```bash
python manage.py createsuperuser
```

7. **Charger les paramètres système (REQUIS)**
```bash
python manage.py loaddata garage/catalog/fixtures/system_settings.json
```

8. **Charger les données de test (optionnel)**
```bash
python generate_test_data.py
```

9. **Lancer le serveur de développement**
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse : `http://127.0.0.1:8000/`

### Réinitialisation du Projet

Pour repartir sur une base propre (suppression de la base de données et des migrations), utilisez le script :

```bash
python reset_db.py
```

Puis réinstallez la base :
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata garage/catalog/fixtures/system_settings.json  # REQUIS
python generate_test_data.py  # Optionnel
```

## Utilisation

### Accès à l'application

- **Page d'accueil :** http://127.0.0.1:8000/
- **Interface d'administration :** http://127.0.0.1:8000/admin/

### Données de Test

Si vous avez exécuté `generate_test_data.py`, vous pouvez vous connecter avec :

**Clients de test :**
- Username: `client1` à `client5`
- Password: `test1234`

**Gestionnaires de test :**
- Username: `gestionnaire1`, `gestionnaire2`
- Password: `test1234`

**Administrateur :**
- Username: `admin`
- Password: `test1234`

### Guide de Démarrage Rapide

**En tant que Client :**

1. Créez un compte ou connectez-vous
2. Allez dans "Mes Véhicules" → "Ajouter un véhicule"
3. Remplissez les informations (immatriculation, marque, modèle, etc.)
4. Allez dans "Mes Dossiers" → "Nouveau dossier"
5. Sélectionnez votre véhicule et décrivez le problème
6. Cliquez sur les boutons de pannes correspondantes
7. Consultez votre devis généré automatiquement
8. Acceptez le devis
9. Réservez un rendez-vous parmi les créneaux disponibles
10. Suivez l'avancement dans la timeline de votre dossier

**En tant que Gestionnaire :**

1. Connectez-vous avec un compte gestionnaire
2. Consultez le tableau de bord des dossiers
3. Cliquez sur un dossier pour voir les détails
4. Révisez et validez le devis si nécessaire
5. Faites progresser le statut du dossier
6. Générez la facture une fois le travail terminé

**En tant qu'Administrateur :**

1. Accédez à l'interface d'administration Django
2. Configurez le catalogue de pannes (groupes et pannes individuelles)
3. Définissez les tarifs (taux horaire, TVA)
4. Créez des créneaux de rendez-vous récurrents
5. Gérez les utilisateurs et leurs rôles

## Structure du Projet

```
projetwebl3-main/
│
├── monsite/                      # Configuration principale Django
│   ├── settings.py              # Paramètres du projet
│   ├── urls.py                  # Routage URL principal
│   └── wsgi.py / asgi.py        # Interfaces serveur
│
├── garage/                       # Application principale (8 modules)
│   ├── accounts/                # Authentification & profils
│   │   ├── models.py           # UserProfile
│   │   ├── views.py            # Vues d'authentification
│   │   └── forms.py            # Formulaires de connexion/inscription
│   │
│   ├── vehicles/                # Gestion des véhicules
│   │   ├── models.py           # Vehicle, VehicleHistory
│   │   ├── views.py            # CRUD véhicules
│   │   └── forms.py            # Formulaires véhicules
│   │
│   ├── cases/                   # Dossiers de réparation
│   │   ├── models.py           # Case, StatusLog
│   │   ├── views.py            # Workflow des dossiers
│   │   └── forms.py            # Formulaires de dossiers
│   │
│   ├── catalog/                 # Catalogue et configuration
│   │   ├── models.py           # FaultGroup, Fault, SystemSettings
│   │   ├── views.py            # Configuration du catalogue
│   │   └── admin.py            # Interface admin personnalisée
│   │
│   ├── quotes/                  # Devis
│   │   ├── models.py           # Quote, QuoteLine
│   │   ├── views.py            # Génération et gestion devis
│   │   └── utils.py            # Génération PDF
│   │
│   ├── appointments/            # Rendez-vous
│   │   ├── models.py           # AppointmentSlot, Appointment
│   │   ├── views.py            # Réservation et gestion
│   │   └── forms.py            # Formulaires rendez-vous
│   │
│   ├── billing/                 # Facturation
│   │   ├── models.py           # Invoice, InvoiceLine, Payment
│   │   ├── views.py            # Génération factures
│   │   └── utils.py            # PDF et paiements
│   │
│   └── notifications/           # Notifications
│       ├── models.py           # Notification
│       ├── views.py            # Affichage notifications
│       └── utils.py            # Création automatique
│
├── templates/                   # Templates Django
│   ├── base.html               # Template de base
│   ├── accounts/               # Templates authentification
│   ├── vehicles/               # Templates véhicules
│   ├── cases/                  # Templates dossiers
│   ├── quotes/                 # Templates devis
│   ├── appointments/           # Templates rendez-vous
│   ├── billing/                # Templates facturation
│   └── notifications/          # Templates notifications
│
├── static/                      # Fichiers statiques
│   ├── css/                    # Feuilles de style
│   ├── js/                     # JavaScript
│   └── images/                 # Images et icônes
│
├── logs/                        # Logs de l'application
│   └── garage.log              # Fichier de log principal
│
├── cahier de charge/            # Documentation du projet
│   ├── main.tex                # Cahier des charges (LaTeX)
│   └── *.png                   # Diagrammes UML
│
├── requirements.txt             # Dépendances Python
├── .env.example                # Exemple de configuration
├── manage.py                   # CLI Django
├── generate_test_data.py       # Script de génération de données
├── DEMARRAGE_RAPIDE.md         # Guide de démarrage
└── README.md                   # Ce fichier
```

## Modèles de Données

### Relations entre Entités

```
User (Django)
├── UserProfile (rôle: CLIENT, GESTIONNAIRE, ADMIN)
├── Vehicle (propriétaire)
│   └── VehicleHistory (journal d'événements)
├── Case (client)
│   ├── Quote (un-à-un)
│   │   └── QuoteLine (plusieurs)
│   ├── Appointment (un-à-un, optionnel)
│   ├── StatusLog (plusieurs, audit trail)
│   ├── Invoice (un-à-un, optionnel)
│   │   ├── InvoiceLine (plusieurs)
│   │   └── Payment (plusieurs)
│   └── Notification (plusieurs)
└── Notification (notifications de l'utilisateur)

FaultGroup (Groupe de pannes)
└── Fault (plusieurs, un-à-plusieurs)

SystemSettings (singleton - configuration globale)
```

### Workflow des Statuts

```
NOUVEAU
  ↓
DEVIS_ÉMIS
  ↓ (acceptation)        ↓ (refus)
DEVIS_ACCEPTÉ          DEVIS_REFUSÉ
  ↓                        ↓ (expiration)
RDV_CONFIRMÉ            EXPIRÉ
  ↓
EN_COURS
  ↓
PRÊT
  ↓
CLÔTURÉ
```

## Sécurité

### Authentification et Autorisation

- Système d'authentification Django
- Contrôle d'accès basé sur les rôles (RBAC)
- Décorateurs `@login_required` sur les vues sensibles
- Vérification des permissions (clients voient uniquement leurs données)

### Protection des Données

- **Mots de passe :** Hachage Django par défaut (PBKDF2)
- **Sessions :** Timeout de 30 minutes, renouvelées à chaque requête
- **Verrouillage de compte :** Après échecs de connexion multiples
- **CSRF :** Protection sur tous les formulaires
- **XSS :** Protection activée

### Traçabilité

- `StatusLog` : Enregistre tous les changements de statut
- `VehicleHistory` : Journal des événements véhicule
- Numérotation automatique factures/devis
- Suivi utilisateur (qui a changé quoi, quand)

## Méthodologie

### Approche Agile Scrum

- **Taille de l'équipe :** 3 étudiants
- **Durée des sprints :** 1-2 semaines
- **Nombre de sprints :** 3 sprints principaux
- **Rôles :** Product Owner (instructeur), Scrum Master (rotation), Équipe de développement

### Phases du Projet

1. **Sprint 0 :** Analyse et spécifications (recueil des besoins, modélisation UML)
2. **Sprint 1 :** Fonctionnalités de base (auth, véhicules, dossiers, devis basiques)
3. **Sprint 2 :** Fonctionnalités avancées (rendez-vous, facturation, notifications)
4. **Sprint 3 :** Finalisation, tests, documentation

## Équipe

**Projet universitaire L3 MIAGE - Université Paris Nanterre**

- **Baaboura Ritej**
- **Thibaud Thomas Lamotte**
- **Baibou Selma**

**Année universitaire :** 2024/2025
**Date de soutenance :** 12 décembre 2025

---

## Licence

Ce projet est développé dans un cadre académique à l'Université Paris Nanterre.

---

## Contact & Support

Pour toute question ou suggestion concernant ce projet :
- Consultez la documentation dans [cahier de charge/main.tex](cahier%20de%20charge/main.tex)
- Référez-vous au guide de démarrage rapide : [DEMARRAGE_RAPIDE.md](DEMARRAGE_RAPIDE.md)

---

**Développé avec Django 6.0 et Python 3.13+ | Université Paris Nanterre - L3 MIAGE 2025/2026**
