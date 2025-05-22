from django import forms
from recruiter.models import Job
from .models import UserJobPreference

class JobApplicationForm(forms.Form):
    """Form for submitting job applications"""
    cover_letter = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Introduce yourself and explain why you are a good fit for this position'
        }),
        required=True
    )
    resume = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx'
        }),
        required=True,
        help_text='Accepted formats: PDF, DOC, DOCX'
    )
    
    def clean_resume(self):
        resume = self.cleaned_data.get('resume')
        if resume:
            # Check file size (limit to 5MB)
            if resume.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Resume file size must be under 5MB")
            
            # Check file extension
            file_name = resume.name
            if not file_name.lower().endswith(('.pdf', '.doc', '.docx')):
                raise forms.ValidationError("Only PDF, DOC, or DOCX files are allowed")
        
        return resume

class JobSearchForm(forms.Form):
    """Form for searching jobs"""
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by title, skill, or keyword'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Location'
        })
    )
    job_type = forms.ChoiceField(
        choices=[('', 'All Job Types')] + list(Job.JOB_TYPE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

class UserJobPreferenceForm(forms.ModelForm):
    """Form for updating job preferences"""
    class Meta:
        model = UserJobPreference
        fields = [
            'preferred_job_types',
            'preferred_locations',
            'min_salary_expectation',
            'remote_preference',
            'industry_preferences'
        ]
        widgets = {
            'preferred_job_types': forms.CheckboxSelectMultiple(),
            'preferred_locations': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter locations separated by commas'
            }),
            'min_salary_expectation': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimum expected salary'
            }),
            'remote_preference': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'industry_preferences': forms.SelectMultiple(attrs={'class': 'form-select'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['preferred_job_types'].choices = Job.JOB_TYPE_CHOICES
        self.fields['industry_preferences'].choices = [
            ('Technology', 'Technology'),
            ('Healthcare', 'Healthcare'),
            ('Finance', 'Finance'),
            ('Education', 'Education'),
            ('Retail', 'Retail'),
            ('Manufacturing', 'Manufacturing'),
            ('Media', 'Media'),
            ('Construction', 'Construction'),
            ('Transportation', 'Transportation'),
            ('Food Service', 'Food Service'),
        ]