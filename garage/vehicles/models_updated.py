# NOTE: Ajout commentaire pour la méthode save() dans vehicles/models.py
# Remplacer la méthode save() existante (lignes 169-172) par:

def save(self, *args, **kwargs):
    """
    Override save pour appeler clean() avec gestion d'erreur
    Note: full_clean() peut lever ValidationError
    """
    try:
        self.full_clean()
    except ValidationError as e:
        # Re-lever l'erreur pour que Django la gère correctement
        raise e
    super().save(*args, **kwargs)
