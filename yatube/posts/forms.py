from django.forms import ModelForm, Textarea

from .models import Comment, Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': 'Текст поста',
            'group': 'Группа'
        },
        help_texts = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        },
        widgets = {
            'text': Textarea(attrs={'cols': 40, 'rows': 10}),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
