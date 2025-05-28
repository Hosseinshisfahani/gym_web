from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib import messages
from django.urls import reverse

@receiver(post_save, sender='gym.Certificate')
def handle_certificate_approval(sender, instance, created, **kwargs):
    """
    Signal handler for when a certificate is approved
    """
    if instance.status == 'approved' and not created:
        try:
            user_profile = instance.user.userprofile
            
            # Store the approval message in the certificate
            instance.approval_message = (
                f'گواهی شما با موفقیت تایید شد.\n'
                f'تاریخ تایید: {timezone.now().strftime("%Y-%m-%d")}'
            )
            instance.save(update_fields=['approval_message'])
            print(f"Certificate approved for {instance.user.username}")
        except Exception as e:
            print(f"Error in certificate approval handler: {str(e)}") 