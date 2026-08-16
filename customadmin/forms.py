import re
from django import forms
from .models import Category

class CategoryForm(forms.ModelForm):

    name = forms.CharField(max_length=100,required=True,widget=forms.TextInput(attrs={"class": "form-control","placeholder": "Enter category name",
                "maxlength": "100","autocomplete": "off",}))

    class Meta:
        model = Category
        fields = ["name"]

    def clean_name(self):

        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Category name cannot be empty.")

        if not re.fullmatch(r"[A-Za-z ]+", name):
            raise forms.ValidationError("Category name can contain only letters and spaces.")

        if "  " in name:
            raise forms.ValidationError("Category name cannot contain multiple consecutive spaces.")

        existing = Category.objects.filter(name__iexact=name,is_trashed=False)

        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)

        if existing.exists():
            raise forms.ValidationError("This category already exists.")

        return name