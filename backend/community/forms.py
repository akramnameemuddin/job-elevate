from django import forms
from .models import Post, Comment, Tag

class PostForm(forms.ModelForm):
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select relevant tags for your post"
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'post_type', 'image', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title...',
                'required': True
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'Share your thoughts, questions, or resources...',
                'required': True
            }),
            'post_type': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update({'required': True})
        self.fields['content'].widget.attrs.update({'required': True})
        self.fields['post_type'].widget.attrs.update({'required': True})
        self.fields['tags'].widget = forms.CheckboxSelectMultiple(attrs={
            'class': 'tag-checkbox-input'
        })
        self.fields['tags'].help_text = "Select relevant tags for your post"
        
        # Set queryset for tags to ensure they're always available
        self.fields['tags'].queryset = Tag.objects.all().order_by('name')
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or len(title.strip()) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title.strip()
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 10:
            raise forms.ValidationError("Content must be at least 10 characters long.")
        return content.strip()

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment...',
                'required': True
            })
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or len(content.strip()) < 3:
            raise forms.ValidationError("Comment must be at least 3 characters long.")
        return content.strip()

class PostFilterForm(forms.Form):
    POST_TYPE_CHOICES = [
        ('all', 'All Types'),
        ('discussion', 'Discussion'),
        ('question', 'Question'),
        ('announcement', 'Announcement'),
        ('job_sharing', 'Job Sharing'),
        ('resource', 'Resource'),
    ]
    
    SORT_CHOICES = [
        ('recent', 'Most Recent'),
        ('popular', 'Most Popular'),
        ('most_viewed', 'Most Viewed'),
    ]
    
    type = forms.ChoiceField(
        choices=POST_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    sort = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search posts, users, or content...'
        })
    )
    
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label="All Tags",
        widget=forms.Select(attrs={'class': 'form-control'})
    )