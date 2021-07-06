from django.apps import AppConfig


class AgendaAppConfig(AppConfig):
    name = "openslides.agenda"
    verbose_name = "OpenSlides Agenda"

    def ready(self):
        # Import all required stuff.
        from django.db.models.signals import post_save, pre_delete

        from ..core.signals import permission_change
        from ..utils.rest_api import router
        from . import serializers  # noqa
        from .signals import (
            get_permission_change_data,
            listen_to_related_object_post_delete,
            listen_to_related_object_post_save,
        )
        from .views import ItemViewSet, ListOfSpeakersViewSet, SpeakerViewSet

        # Connect signals.
        post_save.connect(
            listen_to_related_object_post_save,
            dispatch_uid="listen_to_related_object_post_save",
        )
        pre_delete.connect(
            listen_to_related_object_post_delete,
            dispatch_uid="listen_to_related_object_post_delete",
        )
        permission_change.connect(
            get_permission_change_data, dispatch_uid="agenda_get_permission_change_data"
        )

        # Register viewsets.
        router.register(self.get_model("Item").get_collection_string(), ItemViewSet)
        router.register(
            self.get_model("ListOfSpeakers").get_collection_string(),
            ListOfSpeakersViewSet,
        )
        router.register(
            self.get_model("Speaker").get_collection_string(),
            SpeakerViewSet,
        )

    def get_config_variables(self):
        from .config_variables import get_config_variables

        return get_config_variables()

    def get_startup_elements(self):
        """
        Yields all Cachables required on startup i. e. opening the websocket
        connection.
        """
        yield self.get_model("Item")
        yield self.get_model("ListOfSpeakers")
