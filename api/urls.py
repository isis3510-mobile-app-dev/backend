from django.urls import path
from api.views.pet_views import (
    create_pet,
    pet_detail,
    medical_history,
    vaccinations,
)
from api.views.vaccine_views import (
    create_vaccine_view,
    get_vaccine_view,
    update_vaccine_view,
    delete_vaccine_view,
    list_vaccines_view,
)
from api.views.user_views import UserView

urlpatterns = [
    # Pets CRUD
    path("pets/", create_pet, name="pets-list"),
    path("pets/<str:pet_id>/", pet_detail, name="pet-detail"),

    # Embedded resources
    path("pets/<str:pet_id>/medical-history/", medical_history),
    path("pets/<str:pet_id>/vaccinations/", vaccinations),

    # Vaccines CRUD
     path("vaccines/", list_vaccines_view, name="list_vaccines"),
    path("vaccines/create/", create_vaccine_view, name="create_vaccine"),
    path("vaccines/<str:vaccine_id>/", get_vaccine_view, name="get_vaccine"),
    path("vaccines/<str:vaccine_id>/update/", update_vaccine_view, name="update_vaccine"),
    path("vaccines/<str:vaccine_id>/delete/", delete_vaccine_view, name="delete_vaccine"),
    path("user/", UserView.as_view(), name="user"),
]