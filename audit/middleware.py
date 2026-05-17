from .models import AuditLog
class AuditMiddleware:
 def __init__(self,get_response): self.get_response=get_response
 def __call__(self,request):
  response=self.get_response(request)
  if request.method in ('POST','PUT','PATCH','DELETE'):
   user=request.user if getattr(request,'user',None) and request.user.is_authenticated else None
   AuditLog.objects.create(user=user,action=request.method,path=request.path[:255],method=request.method,ip_address=request.META.get('REMOTE_ADDR'))
  return response
