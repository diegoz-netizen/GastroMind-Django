from django.apps import apps
from django.test.runner import DiscoverRunner


class UnmanagedModelsTestRunner(DiscoverRunner):
    """
    En producción los modelos de catalogo son managed = False (las tablas las crea script_database.sql).
    Solo durante los tests se vuelven managed para que Django cree esas tablas en la BD de prueba.
    """

    def setup_test_environment(self, *args, **kwargs):
        self._no_gestionados = [m for m in apps.get_app_config('catalogo').get_models() if not m._meta.managed]
        for modelo in self._no_gestionados:
            modelo._meta.managed = True
        super().setup_test_environment(*args, **kwargs)

    def teardown_test_environment(self, *args, **kwargs):
        super().teardown_test_environment(*args, **kwargs)
        for modelo in self._no_gestionados:
            modelo._meta.managed = False
