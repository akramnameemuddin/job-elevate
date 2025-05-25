from django import forms
from django.contrib.auth import get_user_model
from .models import Post, Comment, Tag

User = get_user_model()

class PostForm(forms.ModelForm):
    tags = forms.CharField(
        required=False,
        help_text="Enter tags separated by commas (e.g., python, django, web-dev)",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter tags separated by commas'
        })
    )
    
    class Meta:
        model = Post
        fields = ['title', 'content', 'post_type', 'image']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter post title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Write your post content here...'
            }),
            'post_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing post, populate tags field
        if self.instance.pk:
            self.fields['tags'].initial = ', '.join([tag.name for tag in self.instance.tags.all()])
    
    def clean_tags(self):
        tags_str = self.cleaned_data.get('tags', '')
        if not tags_str:
            return []
        
        # Split by comma and clean each tag
        tag_names = [tag.strip().lower() for tag in tags_str.split(',') if tag.strip()]
        
        # Remove duplicates while preserving order
        unique_tags = []
        for tag in tag_names:
            if tag not in unique_tags and len(tag) <= 50:  # Max length check
                unique_tags.append(tag)
        
        return unique_tags[:10]  # Limit to 10 tags
    
    def save(self, commit=True):
        instance = super().save(commit=commit)
        
        if commit:
            # Handle tags
            tag_names = self.cleaned_data.get('tags', [])
            if tag_names:
                # Clear existing tags
                instance.tags.clear()
                
                # Create or get tags and add them to the post
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'slug': tag_name.replace(' ', '-')}
                    )
                    instance.tags.add(tag)
        
        return instance

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write your comment here...',
                'required': True
            })
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content')
        if not content or not content.strip():
            raise forms.ValidationError("Comment cannot be empty.")
        if len(content) > 1000:
            raise forms.ValidationError("Comment is too long. Maximum 1000 characters allowed.")
        return content.strip()

class PostFilterForm(forms.Form):
    POST_TYPE_CHOICES = [
        ('all', 'All Posts'),
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
    
    tag = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    )

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tag name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter tag description (optional)'
            })
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError("Tag name is required.")
        
        # Convert to lowercase and remove extra spaces
        name = name.lower().strip()
        
        # Check if tag already exists (for new tags)
        if not self.instance.pk and Tag.objects.filter(name=name).exists():
            raise forms.ValidationError("A tag with this name already exists.")
        
        return name