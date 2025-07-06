# account/context_processors.py

from user_auths.models import User

def admin_pending_count(request):
    count = User.objects.filter(role='ADMIN', is_active=False).count()
    return {
        'admin_pending_count': count
    }
