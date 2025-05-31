from django.forms import ModelForm
from .models import Room

class RoomForm(ModelForm):
    """
    Form for creating or updating a Room.
    """
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']