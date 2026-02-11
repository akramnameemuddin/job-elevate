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

    # Override fields to handle JSON data properly
    preferred_job_types = forms.MultipleChoiceField(
        choices=Job.JOB_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'job-type-checkbox'}),
        required=False
    )

    preferred_locations = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    industry_preferences = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = UserJobPreference
        fields = [
            'preferred_job_types',
            'preferred_locations',
            'min_salary_expectation',
            'max_salary_expectation',
            'salary_currency',
            'salary_period',
            'remote_preference',
            'industry_preferences',
            'experience_level',
        ]
        widgets = {
            'min_salary_expectation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000',
                'placeholder': 'e.g. 500000'
            }),
            'max_salary_expectation': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1000',
                'placeholder': 'e.g. 1200000'
            }),
            'salary_currency': forms.Select(attrs={
                'class': 'form-select',
            }),
            'salary_period': forms.Select(attrs={
                'class': 'form-select',
            }),
            'remote_preference': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'experience_level': forms.Select(
                choices=[
                    ('', 'Select experience level'),
                    ('fresher', 'Fresher (0-1 years)'),
                    ('junior', 'Junior (1-3 years)'),
                    ('mid', 'Mid Level (3-5 years)'),
                    ('senior', 'Senior (5-8 years)'),
                    ('lead', 'Lead (8-12 years)'),
                    ('principal', 'Principal (12+ years)'),
                ],
                attrs={'class': 'form-select'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values for JSON fields
        if self.instance and self.instance.pk:
            if self.instance.preferred_job_types:
                self.fields['preferred_job_types'].initial = self.instance.preferred_job_types
            if self.instance.preferred_locations:
                self.fields['preferred_locations'].initial = ','.join(self.instance.preferred_locations)
            if self.instance.industry_preferences:
                self.fields['industry_preferences'].initial = ','.join(self.instance.industry_preferences)

    def clean_preferred_locations(self):
        """Convert comma-separated string to list"""
        locations_data = self.cleaned_data.get('preferred_locations', '')
        if isinstance(locations_data, list):
            return locations_data
        if locations_data:
            return [loc.strip() for loc in locations_data.split(',') if loc.strip()]
        return []

    def clean_industry_preferences(self):
        """Convert comma-separated string to list"""
        industries_data = self.cleaned_data.get('industry_preferences', '')
        if isinstance(industries_data, list):
            return industries_data
        if industries_data:
            return [ind.strip() for ind in industries_data.split(',') if ind.strip()]
        return []

    def clean_preferred_job_types(self):
        """Ensure job types is a list"""
        job_types = self.cleaned_data.get('preferred_job_types', [])
        return list(job_types) if job_types else []
    
    def clean(self):
        cleaned_data = super().clean()
        min_sal = cleaned_data.get('min_salary_expectation')
        max_sal = cleaned_data.get('max_salary_expectation')
        if min_sal and max_sal and min_sal > max_sal:
            raise forms.ValidationError("Minimum salary cannot be greater than maximum salary.")
        return cleaned_data