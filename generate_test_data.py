#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de génération de données de test complètes pour GaragePlus
Génère des utilisateurs, véhicules, dossiers, devis, rendez-vous, factures, etc.
"""

import os
import sys
import io

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monsite.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from garage.accounts.models import UserProfile
from garage.vehicles.models import Vehicle, VehicleHistory
from garage.catalog.models import FaultGroup, Fault, SystemSettings
from garage.cases.models import Case, StatusLog
from garage.quotes.models import Quote, QuoteLine
from garage.appointments.models import Appointment, AppointmentSlot
from garage.billing.models import Invoice, InvoiceLine, Payment
from garage.notifications.models import Notification


# =============================================================================
# DONNÉES DE TEST
# =============================================================================

CLIENTS_DATA = [
    {
        'username': 'client1',
        'password': 'test1234',
        'first_name': 'Jean',
        'last_name': 'Dupont',
        'email': 'jean.dupont@email.fr',
        'phone': '06 12 34 56 78',
        'address': '12 Rue de la République\n75001 Paris'
    },
    {
        'username': 'client2',
        'password': 'test1234',
        'first_name': 'Marie',
        'last_name': 'Martin',
        'email': 'marie.martin@email.fr',
        'phone': '06 23 45 67 89',
        'address': '45 Avenue des Champs\n69002 Lyon'
    },
    {
        'username': 'client3',
        'password': 'test1234',
        'first_name': 'Pierre',
        'last_name': 'Bernard',
        'email': 'pierre.bernard@email.fr',
        'phone': '06 34 56 78 90',
        'address': '78 Boulevard Victor Hugo\n31000 Toulouse'
    },
    {
        'username': 'client4',
        'password': 'test1234',
        'first_name': 'Sophie',
        'last_name': 'Dubois',
        'email': 'sophie.dubois@email.fr',
        'phone': '06 45 67 89 01',
        'address': '23 Rue du Commerce\n13001 Marseille'
    },
    {
        'username': 'client5',
        'password': 'test1234',
        'first_name': 'Lucas',
        'last_name': 'Leroy',
        'email': 'lucas.leroy@email.fr',
        'phone': '06 56 78 90 12',
        'address': '56 Avenue de la Liberté\n44000 Nantes'
    },
]

GESTIONNAIRES_DATA = [
    {
        'username': 'gestionnaire1',
        'password': 'test1234',
        'first_name': 'Marc',
        'last_name': 'Technicien',
        'email': 'marc.tech@garage-auto-express.fr',
    },
    {
        'username': 'gestionnaire2',
        'password': 'test1234',
        'first_name': 'Julie',
        'last_name': 'Manager',
        'email': 'julie.manager@garage-auto-express.fr',
    },
]

VEHICLES_DATA = [
    # Client 1
    {'brand': 'Peugeot', 'model': '208', 'year': 2020, 'plate': 'AB-123-CD', 'mileage': 45000, 'fuel': 'ESSENCE'},
    {'brand': 'Renault', 'model': 'Clio', 'year': 2019, 'plate': 'EF-456-GH', 'mileage': 62000, 'fuel': 'DIESEL'},
    # Client 2
    {'brand': 'Citroën', 'model': 'C3', 'year': 2021, 'plate': 'IJ-789-KL', 'mileage': 28000, 'fuel': 'ESSENCE'},
    # Client 3
    {'brand': 'Volkswagen', 'model': 'Golf', 'year': 2018, 'plate': 'MN-012-OP', 'mileage': 78000, 'fuel': 'DIESEL'},
    {'brand': 'BMW', 'model': 'Serie 3', 'year': 2022, 'plate': 'QR-345-ST', 'mileage': 15000, 'fuel': 'HYBRIDE'},
    # Client 4
    {'brand': 'Mercedes', 'model': 'Classe A', 'year': 2020, 'plate': 'UV-678-WX', 'mileage': 52000, 'fuel': 'DIESEL'},
    # Client 5
    {'brand': 'Toyota', 'model': 'Yaris', 'year': 2021, 'plate': 'YZ-901-AB', 'mileage': 32000, 'fuel': 'HYBRIDE'},
    {'brand': 'Audi', 'model': 'A3', 'year': 2019, 'plate': 'CD-234-EF', 'mileage': 68000, 'fuel': 'ESSENCE'},
]

PROBLEMES_DESCRIPTIONS = [
    "Bruit étrange au niveau du moteur lors de l'accélération. Le véhicule perd également de la puissance en montée.",
    "Voyant moteur allumé depuis 3 jours. Démarrage difficile le matin à froid.",
    "Freins qui grincent fortement lors du freinage. Sensation de vibrations dans la pédale.",
    "Climatisation ne fonctionne plus. Air chaud qui sort même en mode froid.",
    "Problème d'embrayage : pédale qui devient molle et difficultés à passer les vitesses.",
    "Fuite d'huile sous le véhicule. Niveau d'huile qui baisse rapidement.",
    "Batterie qui se décharge rapidement. Problèmes de démarrage fréquents.",
    "Suspension arrière affaissée. Bruits de claquements sur les dos d'âne.",
]


# =============================================================================
# FONCTIONS DE GÉNÉRATION
# =============================================================================

def print_section(title):
    """Affiche un titre de section"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def create_users():
    """Crée les utilisateurs (clients, gestionnaires, admin)"""
    print_section("CRÉATION DES UTILISATEURS")

    users = {}

    # Admin
    if not User.objects.filter(username='admin').exists():
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@garage-auto-express.fr',
            password='admin1234',
            first_name='Admin',
            last_name='Système'
        )
        admin.profile.role = 'ADMIN'
        admin.profile.save()
        users['admin'] = admin
        print(f"✓ Admin créé: admin / admin1234")

    # Clients
    clients = []
    for i, data in enumerate(CLIENTS_DATA, 1):
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email']
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
            user.profile.role = 'CLIENT'
            user.profile.phone_number = data['phone']
            user.profile.address = data['address']
            user.profile.save()
            print(f"✓ Client {i} créé: {data['username']} / {data['password']}")
        else:
            user.profile.role = 'CLIENT'
            user.profile.phone_number = data['phone']
            user.profile.address = data['address']
            user.profile.save()
            print(f"✓ Client {i} déjà existant: {data['username']}")
        clients.append(user)

    users['clients'] = clients

    # Gestionnaires
    gestionnaires = []
    for i, data in enumerate(GESTIONNAIRES_DATA, 1):
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email']
            }
        )
        if created:
            user.set_password(data['password'])
            user.save()
            print(f"✓ Gestionnaire {i} créé: {data['username']} / {data['password']}")
        else:
            print(f"✓ Gestionnaire {i} déjà existant: {data['username']}")
        user.profile.role = 'GESTIONNAIRE'
        user.profile.save()
        gestionnaires.append(user)

    users['gestionnaires'] = gestionnaires

    print(f"\n✓ Total: {len(clients)} clients, {len(gestionnaires)} gestionnaires, 1 admin")
    return users


def create_vehicles(users):
    """Crée les véhicules pour les clients"""
    print_section("CRÉATION DES VÉHICULES")

    vehicles = []
    client_index = 0
    clients = users['clients']

    vehicle_distribution = [2, 1, 2, 1, 2]  # Nombre de véhicules par client

    for i, vdata in enumerate(VEHICLES_DATA):
        if client_index < len(clients):
            owner = clients[client_index]

            vehicle = Vehicle.objects.create(
                owner=owner,
                brand=vdata['brand'],
                model=vdata['model'],
                year=vdata['year'],
                plate_number=vdata['plate'],
                mileage=vdata['mileage'],
                fuel_type=vdata['fuel'],
                insurance_company=random.choice(['AXA', 'MAIF', 'Allianz', 'Generali', 'MACIF']),
                insurance_expiry_date=timezone.now().date() + timedelta(days=random.randint(30, 365))
            )
            vehicles.append(vehicle)

            # Historique
            VehicleHistory.objects.create(
                vehicle=vehicle,
                event_type='CREATION',
                description=f"Véhicule {vehicle} ajouté au système"
            )

            print(f"✓ Véhicule créé: {vehicle} (Propriétaire: {owner.get_full_name()})")

            # Passer au client suivant si on a créé tous ses véhicules
            if (i + 1) >= sum(vehicle_distribution[:client_index + 1]):
                client_index += 1

    print(f"\n✓ Total: {len(vehicles)} véhicules créés")
    return vehicles


def create_fault_catalog():
    """Crée le catalogue de pannes si nécessaire"""
    print_section("VÉRIFICATION DU CATALOGUE DE PANNES")

    if Fault.objects.count() == 0:
        print("⚠ Catalogue vide. Création du catalogue de base...")

        # Groupes de pannes
        groups_data = [
            {'name': 'Moteur', 'icon': 'fa-engine', 'order': 1},
            {'name': 'Freinage', 'icon': 'fa-brake', 'order': 2},
            {'name': 'Électricité', 'icon': 'fa-bolt', 'order': 3},
            {'name': 'Pneumatiques', 'icon': 'fa-tire', 'order': 4},
            {'name': 'Climatisation', 'icon': 'fa-snowflake', 'order': 5},
        ]

        for gdata in groups_data:
            FaultGroup.objects.get_or_create(
                name=gdata['name'],
                defaults={'order': gdata['order']}
            )

        # Pannes par groupe
        faults_data = [
            # Moteur
            ('Moteur', 'Vidange moteur', 'Remplacement huile moteur + filtre', 1.0, 80.0),
            ('Moteur', 'Remplacement courroie distribution', 'Courroie + galets tendeurs', 3.5, 250.0),
            ('Moteur', 'Remplacement bougies', 'Changement des 4 bougies d\'allumage', 1.0, 60.0),

            # Freinage
            ('Freinage', 'Plaquettes de frein avant', 'Remplacement plaquettes AV', 1.5, 120.0),
            ('Freinage', 'Disques de frein avant', 'Remplacement disques + plaquettes AV', 2.0, 280.0),
            ('Freinage', 'Plaquettes de frein arrière', 'Remplacement plaquettes AR', 1.5, 100.0),

            # Électricité
            ('Électricité', 'Batterie', 'Remplacement batterie 12V', 0.5, 150.0),
            ('Électricité', 'Alternateur', 'Remplacement alternateur', 2.5, 380.0),
            ('Électricité', 'Démarreur', 'Remplacement démarreur', 2.0, 320.0),

            # Pneumatiques
            ('Pneumatiques', 'Changement 4 pneus', 'Pneus neufs + équilibrage', 1.5, 400.0),
            ('Pneumatiques', 'Géométrie', 'Réglage géométrie 4 roues', 1.0, 80.0),

            # Climatisation
            ('Climatisation', 'Recharge climatisation', 'Recharge gaz + contrôle étanchéité', 1.0, 120.0),
            ('Climatisation', 'Filtre habitacle', 'Remplacement filtre d\'habitacle', 0.5, 35.0),
        ]

        for group_name, fault_name, desc, hours, parts in faults_data:
            group = FaultGroup.objects.get(name=group_name)
            Fault.objects.create(
                group=group,
                name=fault_name,
                description=desc,
                labor_hours=Decimal(str(hours)),
                parts_cost=Decimal(str(parts)),
                is_active=True
            )

        print(f"✓ {Fault.objects.count()} pannes créées")
    else:
        print(f"✓ Catalogue déjà présent ({Fault.objects.count()} pannes)")

    # Vérifier SystemSettings
    if SystemSettings.objects.count() == 0:
        print("⚠ Pas de paramètres système. Charger la fixture system_settings.json")
    else:
        print(f"✓ Paramètres système présents")


def create_appointment_slots():
    """Crée les créneaux de rendez-vous"""
    print_section("VÉRIFICATION DES CRÉNEAUX RDV")

    if AppointmentSlot.objects.count() == 0:
        print("⚠ Créneaux vides. Création des créneaux...")

        # Lundi à Vendredi: 9h-12h et 14h-17h
        for day in range(5):  # 0=Lundi, 4=Vendredi
            # Matin
            AppointmentSlot.objects.create(
                is_recurring=True,
                weekday=day,
                start_time='09:00',
                end_time='10:00',
                is_available=True
            )
            AppointmentSlot.objects.create(
                is_recurring=True,
                weekday=day,
                start_time='10:00',
                end_time='11:00',
                is_available=True
            )
            AppointmentSlot.objects.create(
                is_recurring=True,
                weekday=day,
                start_time='11:00',
                end_time='12:00',
                is_available=True
            )

            # Après-midi
            AppointmentSlot.objects.create(
                is_recurring=True,
                weekday=day,
                start_time='14:00',
                end_time='15:00',
                is_available=True
            )
            AppointmentSlot.objects.create(
                is_recurring=True,
                weekday=day,
                start_time='15:00',
                end_time='16:00',
                is_available=True
            )
            AppointmentSlot.objects.create(
                is_recurring=True,
                weekday=day,
                start_time='16:00',
                end_time='17:00',
                is_available=True
            )

        print(f"✓ {AppointmentSlot.objects.count()} créneaux créés")
    else:
        print(f"✓ Créneaux déjà présents ({AppointmentSlot.objects.count()} créneaux)")


def create_cases_and_workflow(vehicles, users):
    """Crée des dossiers avec workflow complet"""
    print_section("CRÉATION DES DOSSIERS ET WORKFLOW")

    cases_data = []

    # Workflow: NOUVEAU → DEVIS_EMIS → DEVIS_ACCEPTE → RDV_CONFIRME → EN_COURS → PRET → CLOTURE

    # Cas 1: Client 1, Peugeot 208 - CLOTURE (workflow complet)
    cases_data.append({
        'vehicle': vehicles[0],
        'description': PROBLEMES_DESCRIPTIONS[0],
        'urgency': 'NORMALE',
        'status': 'CLOTURE',
        'workflow': ['NOUVEAU', 'DEVIS_EMIS', 'DEVIS_ACCEPTE', 'RDV_CONFIRME', 'EN_COURS', 'PRET', 'CLOTURE'],
        'faults': ['Vidange moteur', 'Remplacement bougies'],
        'has_appointment': True,
        'has_invoice': True,
        'is_paid': True,
        'days_ago': 30
    })

    # Cas 2: Client 1, Renault Clio - PRET (en attente récupération)
    cases_data.append({
        'vehicle': vehicles[1],
        'description': PROBLEMES_DESCRIPTIONS[2],
        'urgency': 'HAUTE',
        'status': 'PRET',
        'workflow': ['NOUVEAU', 'DEVIS_EMIS', 'DEVIS_ACCEPTE', 'RDV_CONFIRME', 'EN_COURS', 'PRET'],
        'faults': ['Plaquettes de frein avant', 'Disques de frein avant'],
        'has_appointment': True,
        'has_invoice': True,
        'is_paid': False,
        'days_ago': 2
    })

    # Cas 3: Client 2, Citroën C3 - EN_COURS
    cases_data.append({
        'vehicle': vehicles[2],
        'description': PROBLEMES_DESCRIPTIONS[3],
        'urgency': 'NORMALE',
        'status': 'EN_COURS',
        'workflow': ['NOUVEAU', 'DEVIS_EMIS', 'DEVIS_ACCEPTE', 'RDV_CONFIRME', 'EN_COURS'],
        'faults': ['Recharge climatisation', 'Filtre habitacle'],
        'has_appointment': True,
        'has_invoice': False,
        'is_paid': False,
        'days_ago': 1
    })

    # Cas 4: Client 3, VW Golf - RDV_CONFIRME (RDV dans 3 jours)
    cases_data.append({
        'vehicle': vehicles[3],
        'description': PROBLEMES_DESCRIPTIONS[4],
        'urgency': 'HAUTE',
        'status': 'RDV_CONFIRME',
        'workflow': ['NOUVEAU', 'DEVIS_EMIS', 'DEVIS_ACCEPTE', 'RDV_CONFIRME'],
        'faults': ['Remplacement courroie distribution'],
        'has_appointment': True,
        'has_invoice': False,
        'is_paid': False,
        'days_ago': -3  # Dans 3 jours
    })

    # Cas 5: Client 3, BMW Serie 3 - DEVIS_ACCEPTE (doit prendre RDV)
    cases_data.append({
        'vehicle': vehicles[4],
        'description': PROBLEMES_DESCRIPTIONS[5],
        'urgency': 'BASSE',
        'status': 'DEVIS_ACCEPTE',
        'workflow': ['NOUVEAU', 'DEVIS_EMIS', 'DEVIS_ACCEPTE'],
        'faults': ['Vidange moteur', 'Filtre habitacle'],
        'has_appointment': False,
        'has_invoice': False,
        'is_paid': False,
        'days_ago': 5
    })

    # Cas 6: Client 4, Mercedes Classe A - DEVIS_EMIS (en attente validation client)
    cases_data.append({
        'vehicle': vehicles[5],
        'description': PROBLEMES_DESCRIPTIONS[6],
        'urgency': 'HAUTE',
        'status': 'DEVIS_EMIS',
        'workflow': ['NOUVEAU', 'DEVIS_EMIS'],
        'faults': ['Batterie', 'Alternateur'],
        'has_appointment': False,
        'has_invoice': False,
        'is_paid': False,
        'days_ago': 2
    })

    # Cas 7: Client 5, Toyota Yaris - NOUVEAU (vient d'être créé)
    cases_data.append({
        'vehicle': vehicles[6],
        'description': PROBLEMES_DESCRIPTIONS[7],
        'urgency': 'NORMALE',
        'status': 'NOUVEAU',
        'workflow': ['NOUVEAU'],
        'faults': ['Géométrie'],
        'has_appointment': False,
        'has_invoice': False,
        'is_paid': False,
        'days_ago': 0
    })

    settings = SystemSettings.objects.first()
    gestionnaire = users['gestionnaires'][0]

    for i, cdata in enumerate(cases_data, 1):
        print(f"\n--- Dossier {i}: {cdata['vehicle']} ---")

        # Créer le dossier
        case = Case.objects.create(
            client=cdata['vehicle'].owner,
            vehicle=cdata['vehicle'],
            description=cdata['description'],
            urgency_level=cdata['urgency'],
            status=cdata['status'],
            created_at=timezone.now() - timedelta(days=abs(cdata['days_ago']))
        )

        # Ajouter les pannes
        faults = Fault.objects.filter(name__in=cdata['faults'])
        case.faults.add(*faults)
        print(f"  ✓ Dossier #{case.id} créé: {cdata['status']}")
        print(f"    Pannes: {', '.join(cdata['faults'])}")

        # Logs de statut
        for j, status in enumerate(cdata['workflow']):
            old_status = cdata['workflow'][j-1] if j > 0 else ''
            StatusLog.objects.create(
                case=case,
                old_status=old_status,
                new_status=status,
                changed_by=gestionnaire if j > 0 else case.client,
                changed_at=case.created_at + timedelta(hours=j*2)
            )

        # Créer le devis si nécessaire
        if cdata['status'] != 'NOUVEAU':
            quote = Quote.objects.create(
                case=case,
                vat_rate=settings.vat_rate,
                created_at=case.created_at + timedelta(hours=2)
            )

            # Lignes de devis
            for fault in faults:
                # Main d'œuvre
                QuoteLine.objects.create(
                    quote=quote,
                    line_type='LABOR',
                    description=f"Main d'œuvre - {fault.name}",
                    hours=fault.labor_hours,
                    hourly_rate=settings.hourly_rate
                )

                # Pièces
                QuoteLine.objects.create(
                    quote=quote,
                    line_type='PARTS',
                    description=f"Pièces - {fault.name}",
                    quantity=1,
                    unit_price_ht=fault.parts_cost
                )

            quote.calculate_totals()

            # Valider le devis si accepté
            if cdata['status'] not in ['NOUVEAU', 'DEVIS_EMIS']:
                quote.is_validated_by_manager = True
                quote.is_accepted_by_client = True
                quote.acceptance_date = quote.created_at + timedelta(hours=4)
                quote.save()
                print(f"  ✓ Devis #{quote.quote_number}: {quote.total_ttc}€ TTC (ACCEPTÉ)")
            else:
                quote.is_validated_by_manager = True
                quote.save()
                print(f"  ✓ Devis #{quote.quote_number}: {quote.total_ttc}€ TTC (EN ATTENTE)")

        # Créer le RDV si nécessaire
        if cdata['has_appointment']:
            if cdata['days_ago'] < 0:
                # RDV futur
                rdv_date = timezone.now().date() + timedelta(days=abs(cdata['days_ago']))
            else:
                # RDV passé
                rdv_date = case.created_at.date() + timedelta(days=3)

            appointment = Appointment.objects.create(
                case=case,
                date=rdv_date,
                start_time='09:00',
                end_time='11:00',
                created_at=case.created_at + timedelta(hours=6)
            )
            print(f"  ✓ RDV: {appointment.date.strftime('%d/%m/%Y')} à 09:00")

        # Créer la facture si nécessaire
        if cdata['has_invoice']:
            invoice = Invoice.objects.create(
                case=case,
                related_quote=case.quote,
                total_ht=case.quote.total_ht,
                vat_rate=case.quote.vat_rate,
                total_vat=case.quote.total_vat,
                total_ttc=case.quote.total_ttc,
                is_paid=cdata['is_paid'],
                created_at=case.created_at + timedelta(days=abs(cdata['days_ago']) - 1)
            )

            # Copier les lignes du devis
            for line in case.quote.lines.all():
                InvoiceLine.objects.create(
                    invoice=invoice,
                    description=line.description,
                    quantity=1,
                    unit_price_ht=line.total_ht,
                    total_ht=line.total_ht
                )

            # Créer le paiement si payé
            if cdata['is_paid']:
                payment = Payment.objects.create(
                    invoice=invoice,
                    amount=invoice.total_ttc,
                    payment_method=random.choice(['CARD', 'CASH', 'CHECK']),
                    status='COMPLETED',
                    completed_at=invoice.created_at + timedelta(hours=2)
                )
                invoice.payment_date = payment.completed_at
                invoice.save()
                print(f"  ✓ Facture #{invoice.invoice_number}: {invoice.total_ttc}€ (PAYÉE)")
            else:
                print(f"  ✓ Facture #{invoice.invoice_number}: {invoice.total_ttc}€ (IMPAYÉE)")

        # Créer des notifications
        Notification.create_for_case_status_change(case, cdata['status'])

    print(f"\n✓ Total: {len(cases_data)} dossiers créés avec workflow complet")


# =============================================================================
# SCRIPT PRINCIPAL
# =============================================================================

def main():
    """Fonction principale"""
    print("\n")
    print("="*70)
    print("         GENERATION DE DONNEES DE TEST - GARAGEPLUS")
    print("="*70)

    try:
        # 1. Utilisateurs
        users = create_users()

        # 2. Catalogue de pannes
        create_fault_catalog()

        # 3. Créneaux RDV
        create_appointment_slots()

        # 4. Véhicules
        vehicles = create_vehicles(users)

        # 5. Dossiers avec workflow complet
        create_cases_and_workflow(vehicles, users)

        # Résumé final
        print_section("RÉSUMÉ FINAL")
        print(f"✓ Utilisateurs: {User.objects.count()}")
        print(f"  - Clients: {UserProfile.objects.filter(role='CLIENT').count()}")
        print(f"  - Gestionnaires: {UserProfile.objects.filter(role='GESTIONNAIRE').count()}")
        print(f"  - Admins: {UserProfile.objects.filter(role='ADMIN').count()}")
        print(f"\n✓ Véhicules: {Vehicle.objects.count()}")
        print(f"✓ Dossiers: {Case.objects.count()}")
        print(f"  - Nouveau: {Case.objects.filter(status='NOUVEAU').count()}")
        print(f"  - Devis émis: {Case.objects.filter(status='DEVIS_EMIS').count()}")
        print(f"  - Devis accepté: {Case.objects.filter(status='DEVIS_ACCEPTE').count()}")
        print(f"  - RDV confirmé: {Case.objects.filter(status='RDV_CONFIRME').count()}")
        print(f"  - En cours: {Case.objects.filter(status='EN_COURS').count()}")
        print(f"  - Prêt: {Case.objects.filter(status='PRET').count()}")
        print(f"  - Clôturé: {Case.objects.filter(status='CLOTURE').count()}")
        print(f"\n✓ Devis: {Quote.objects.count()}")
        print(f"✓ Rendez-vous: {Appointment.objects.count()}")
        print(f"✓ Factures: {Invoice.objects.count()}")
        print(f"  - Payées: {Invoice.objects.filter(is_paid=True).count()}")
        print(f"  - Impayées: {Invoice.objects.filter(is_paid=False).count()}")
        print(f"✓ Paiements: {Payment.objects.count()}")
        print(f"✓ Notifications: {Notification.objects.count()}")

        print("\n" + "="*70)
        print("  DONNEES DE TEST GENEREES AVEC SUCCES!")
        print("="*70)

        print("\n>> COMPTES DE TEST:")
        print("\n  Admin:")
        print("    - admin / admin1234")
        print("\n  Gestionnaires:")
        print("    - gestionnaire1 / test1234")
        print("    - gestionnaire2 / test1234")
        print("\n  Clients:")
        for i in range(1, 6):
            print(f"    - client{i} / test1234")

        print("\n>> Lancer le serveur:")
        print("    python manage.py runserver")
        print("    -> http://127.0.0.1:8000")
        print("\n")

    except Exception as e:
        print(f"\n[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
