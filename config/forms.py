from django import forms
from .models import Alimento

class AlimentoForm(forms.ModelForm):
    class Meta:
        model = Alimento
        fields = [
            'nombre', 'marca', 'unidad', 'cantidad_referencia',
            'kcal', 'proteinas', 'carbohidratos', 'azucares', 'grasas', 'saturadas'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'marca': forms.TextInput(attrs={'class': 'form-control'}),
            'unidad': forms.Select(attrs={'class': 'form-select'}),
            'cantidad_referencia': forms.NumberInput(attrs={'class': 'form-control'}),
            'kcal': forms.NumberInput(attrs={'class': 'form-control'}),
            'proteinas': forms.NumberInput(attrs={'class': 'form-control'}),
            'carbohidratos': forms.NumberInput(attrs={'class': 'form-control'}),
            'azucares': forms.NumberInput(attrs={'class': 'form-control'}),
            'grasas': forms.NumberInput(attrs={'class': 'form-control'}),
            'saturadas': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()
        if not nombre:
            raise forms.ValidationError('El nombre es obligatorio.')
        return nombre

    def clean_cantidad_referencia(self):
        cantidad = self.cleaned_data['cantidad_referencia']
        if cantidad <= 0:
            raise forms.ValidationError('La cantidad de referencia debe ser mayor que 0.')
        return cantidad
