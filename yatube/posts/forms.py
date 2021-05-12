from django import forms

from .models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ("text", "group", "image")
        help_texts = {
            "text": 'Введите Ваш комментарий',
            "group": 'Выберите группу',
            "image": 'Выберите картинку'
        }
        error_messages = {
            'text': {
                'required': "Заполните комментарий",
            },
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("text",)
