import pytest

from apps.administration.models import Region


@pytest.mark.django_db
def test_region_str():
    region = Region.objects.create(nom_region="Centre")
    assert str(region) == "Centre"
