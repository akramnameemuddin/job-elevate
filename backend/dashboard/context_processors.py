def dashboard_context(request):
    """
    Context processor to add dashboard-related variables to all templates
    """
    context = {}
    
    if request.user.is_authenticated:
        user = request.user
        
        # Compute initials from full name
        full_name = user.full_name.strip() if user.full_name else ""
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            initials = name_parts[0][0].upper() + name_parts[-1][0].upper()
        elif len(name_parts) == 1:
            initials = name_parts[0][0].upper()
        else:
            initials = "US"
        
        # Calculate job matches
        job_match_count = user.get_job_matches_count()
        
        context.update({
            'user_initials': initials,
            'job_match_count': job_match_count,
        })
    
    return context
