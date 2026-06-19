from django.apps import AppConfig

class ConstructionappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'constructionapp'

    def ready(self):
        import constructionapp.signals
