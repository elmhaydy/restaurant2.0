from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
def role_required(*roles):
 def deco(view):
  @wraps(view)
  @login_required
  def wrapper(request,*a,**kw):
   if request.user.is_superuser or request.user.role in roles: return view(request,*a,**kw)
   raise PermissionDenied
  return wrapper
 return deco
