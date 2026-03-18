from django.urls import path
from api.views.pet_views import (
    pet_collection,
    my_pets,
    pet_detail,
    vaccinations,
    vaccination_detail,
    vaccination_documents,
)
from api.views.vaccine_views import (
    create_vaccine_view,
    get_vaccine_view,
    update_vaccine_view,
    delete_vaccine_view,
    list_vaccines_view,
)
from api.views.user_views import MeView, UserDetailView
from api.views.event_views import event_collection, event_detail, event_documents
from api.views.notification_views import notification_collection, notification_detail
from api.views.screen_views import screen_collection, screen_detail
from api.views.screen_time_log_views import screen_time_log_collection
from api.views.feature_views import feature_collection, feature_detail
from api.views.feature_route_views import feature_route_collection, feature_route_detail
from api.views.feature_execution_log_views import feature_execution_log_collection
from api.views.feature_clicks_log_views import feature_clicks_log_collection
from api.views.nfc_views import nfc_public_read, nfc_payload, nfc_sync

urlpatterns = [
    # Pets CRUD
    path("pets/", pet_collection, name="pets-list"),
    path("pets/mine/", my_pets, name="pets-mine"),
    path("pets/<str:pet_id>/", pet_detail, name="pet-detail"),

    # Pet embedded resources
    path("pets/<str:pet_id>/vaccinations/", vaccinations),
    path("pets/<str:pet_id>/vaccinations/<str:vaccination_id>/", vaccination_detail),
    path("pets/<str:pet_id>/vaccinations/<str:vaccination_id>/documents/", vaccination_documents),

    # Events (standalone collection)
    path("events/", event_collection, name="events-list"),
    path("events/<str:event_id>/", event_detail, name="event-detail"),
    path("events/<str:event_id>/documents/", event_documents, name="event-documents"),

    # Notifications (standalone collection)
    path("notifications/", notification_collection, name="notifications-list"),
    path("notifications/<str:notification_id>/", notification_detail, name="notification-detail"),

    # Vaccines CRUD
    path("vaccines/", list_vaccines_view, name="list_vaccines"),
    path("vaccines/create/", create_vaccine_view, name="create_vaccine"),
    path("vaccines/<str:vaccine_id>/", get_vaccine_view, name="get_vaccine"),
    path("vaccines/<str:vaccine_id>/update/", update_vaccine_view, name="update_vaccine"),
    path("vaccines/<str:vaccine_id>/delete/", delete_vaccine_view, name="delete_vaccine"),

    # User CRUD
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/<str:firebase_uid>/", UserDetailView.as_view(), name="user-detail"),

    # NFC endpoints
    path("nfc/read/<str:pet_id>/", nfc_public_read, name="nfc-public-read"),
    path("pets/<str:pet_id>/nfc-payload/", nfc_payload, name="nfc-payload"),
    path("pets/<str:pet_id>/nfc-sync/", nfc_sync, name="nfc-sync"),

    ### TELEMETRY ###

    # Screens
    path("screens/", screen_collection, name="screens-list"),
    path("screens/<str:screen_id>/", screen_detail, name="screen-detail"),

    # Screen Time Logs
    path("screen-time-logs/", screen_time_log_collection, name="screen-time-logs"),

    # Features
    path("features/", feature_collection, name="features-list"),
    path("features/<str:feature_id>/", feature_detail, name="feature-detail"),

    # Feature Routes
    path("feature-routes/", feature_route_collection, name="feature-routes-list"),
    path("feature-routes/<str:route_id>/", feature_route_detail, name="feature-route-detail"),

    # Feature Execution Logs
    path("feature-execution-logs/", feature_execution_log_collection, name="feature-execution-logs"),

    # Feature Clicks Logs
    path("feature-clicks-logs/", feature_clicks_log_collection, name="feature-clicks-logs"),
]