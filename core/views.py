from django.conf import settings
from django.contrib import messages
from django.core.mail import EmailMessage
from django.shortcuts import redirect, render
from menu.models import Dish


def home_view(request):
    popular_dishes = Dish.objects.filter(
        is_active=True,
        manual_available=True,
        is_popular=True
    ).select_related('category')[:3]

    return render(request, 'public/index.html', {
        'popular_dishes': popular_dishes
    })


def contact_view(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        email = (request.POST.get("email") or "").strip()
        message = (request.POST.get("message") or "").strip()

        if not name or not email or not message:
            messages.error(request, "Veuillez remplir tous les champs du formulaire.")
            return render(request, "public/contact.html")

        recipient = getattr(settings, "CONTACT_RECIPIENT_EMAIL", settings.DEFAULT_FROM_EMAIL)
        subject = f"Nouveau message contact - {name}"
        body = (
            f"Nom: {name}\n"
            f"Email: {email}\n\n"
            f"Message:\n{message}\n"
        )

        mail = EmailMessage(
            subject=subject,
            body=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
            reply_to=[email],
        )

        try:
            mail.send(fail_silently=False)
            messages.success(request, "Votre message a bien été envoyé.")
            return redirect("contact")
        except Exception:
            messages.error(request, "L'envoi du message a échoué. Vérifiez la configuration email.")

    return render(request, 'public/contact.html')
