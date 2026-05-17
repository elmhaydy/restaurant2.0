# admin_panel/utils.py
from .models import ActivityLog

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")


def create_log(request, action_type, module, description, object_id=None):
    ActivityLog.objects.create(
        user=request.user if request.user.is_authenticated else None,
        action_type=action_type,
        module=module,
        description=description,
        object_id=object_id,
        ip_address=get_client_ip(request),
    )