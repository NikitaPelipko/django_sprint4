from .models import Post
from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()


class CreatePostForm(forms.ModelForm):

    pub_date = forms.DateTimeField(
        label='Дата и время публикации',
        required=True,
        widget=forms.DateTimeInput(
            attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }
        ),
        help_text='Если установить дату и время в будущем — '
            'можно делать отложенные публикации.'
    )

    class Meta:
        model = Post
        fields = ('text','location', 'category', 'pub_date')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk and not self.data:
            self.fields['pub_date'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    def clean_pub_date(self):
        """Валидация даты публикации"""
        pub_date = self.cleaned_data.get('pub_date')
        
        if not pub_date:
            raise ValidationError('Укажите дату и время публикации')
        
        return pub_date


class UserProfileForm(forms.ModelForm):
    
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Имя пользователя',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        if self.instance and self.instance.pk:
            self.fields['email_confirm'].initial = self.instance.email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(username=username).exists():
            raise ValidationError('Пользователь с таким именем уже существует')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        email_confirm = cleaned_data.get('email_confirm')
        
        if email and email_confirm and email != email_confirm:
            raise ValidationError('Email и подтверждение email не совпадают')
        
        if email:
            if User.objects.exclude(pk=self.instance.pk).filter(email=email).exists():
                raise ValidationError('Пользователь с таким email уже существует')
        
        return cleaned_data
