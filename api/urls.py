from django.urls import path
from api.views.pet_views import (
    create_pet,
    pet_detail,
    medical_history,
    vaccinations,
)

urlpatterns = [
    # Pets CRUD
    path("pets/", create_pet, name="pets-list"),
    path("pets/<str:pet_id>/", pet_detail, name="pet-detail"),

    # Embedded resources
    path("pets/<str:pet_id>/medical-history/", medical_history),
    path("pets/<str:pet_id>/vaccinations/", vaccinations),
]