# backend/context_processors.py

def user_initials(request):
    if request.user.is_authenticated:
        full_name = request.user.full_name.strip() if request.user.full_name else ""
        name_parts = full_name.split()
        if len(name_parts) >= 2:
            initials = name_parts[0][0].upper() + name_parts[-1][0].upper()
        elif len(name_parts) == 1:
            initials = name_parts[0][0].upper()
        else:
            initials = "US"
    else:
        initials = "US"
    
    return {
        'user_initials': initials
    }
