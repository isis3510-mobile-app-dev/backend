from django.urls import path
from api.models import pet
from api.views.pet_views import (
    pet_collection,
    documents,
    events,
    pet_detail,
    vaccinations,
    notifications
)
from api.views.vaccine_views import (
    create_vaccine_view,
    get_vaccine_view,
    update_vaccine_view,
    delete_vaccine_view,
    list_vaccines_view,
)
from api.views.user_views import MeView, UserDetailView
from api.views.screen_views import screen_collection, screen_detail
from api.views.screen_time_log_views import screen_time_log_collection

urlpatterns = [
    # Pets CRUD
    path("pets/", pet_collection, name="pets-list"),
    path("pets/<str:pet_id>/", pet_detail, name="pet-detail"),

    # Embedded resources
    path("pets/<str:pet_id>/events/", events),
    path("pets/<str:pet_id>/vaccinations/", vaccinations),
    path("pets/<str:pet_id>/notifications/", notifications),
    path("pets/<str:pet_id>/events/<str:event_id>/documents/", documents),
    path("pets/<str:pet_id>/vaccinations/<str:vaccine_id>/documents/", documents),

    # Vaccines CRUD
    path("vaccines/", list_vaccines_view, name="list_vaccines"),
    path("vaccines/create/", create_vaccine_view, name="create_vaccine"),
    path("vaccines/<str:vaccine_id>/", get_vaccine_view, name="get_vaccine"),
    path("vaccines/<str:vaccine_id>/update/", update_vaccine_view, name="update_vaccine"),
    path("vaccines/<str:vaccine_id>/delete/", delete_vaccine_view, name="delete_vaccine"),

    # User CRUD
    path("users/me/", MeView.as_view(), name="user-me"),
    path("users/<str:firebase_uid>/", UserDetailView.as_view(), name="user-detail"),

    ### TELEMETRY ###

    # Screens
    path("screens/", screen_collection, name="screens-list"),
    path("screens/<str:screen_id>/", screen_detail, name="screen-detail"),

    # Screen Time Logs
    path("screen-time-logs/", screen_time_log_collection, name="screen-time-logs"),
]