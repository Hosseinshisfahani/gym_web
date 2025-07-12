"""
Email notification utilities for gym management system
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class EmailNotificationService:
    """Service class for handling email notifications"""
    
    @staticmethod
    def get_base_url(request=None):
        """Get base URL for email links"""
        if request:
            return f"http://{get_current_site(request).domain}"
        return "https://shirneshansport.ir"  # Default production URL
    
    @staticmethod
    def send_shop_order_notification(order, request=None):
        """Send email notification for new shop orders"""
        try:
            from gym.models import EmailNotificationSettings
            
            # Get all admin emails that want shop order notifications
            admin_emails = EmailNotificationSettings.get_active_notification_emails('shop_order')
            
            if not admin_emails:
                logger.info("No admin emails configured for shop order notifications")
                return False
            
            # Prepare email context
            base_url = EmailNotificationService.get_base_url(request)
            context = {
                'order': order,
                'admin_order_url': f"{base_url}/admin/gym_shop/order/{order.id}/change/",
                'admin_dashboard_url': f"{base_url}/admin/",
                'site_name': 'شیرنشان اسپورت',
                'current_date': timezone.now(),
            }
            
            # Render email template
            html_content = render_to_string('gym/emails/shop_order_notification.html', context)
            text_content = strip_tags(html_content)
            
            subject = f"سفارش جدید فروشگاه - {order.order_number}"
            
            # Send email to each admin
            for admin_email in admin_emails:
                try:
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[admin_email],
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()
                    
                    logger.info(f"Shop order notification sent to {admin_email} for order {order.order_number}")
                    
                except Exception as e:
                    logger.error(f"Failed to send shop order notification to {admin_email}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending shop order notification: {str(e)}")
            return False
    
    @staticmethod
    def send_plan_request_notification(plan_request, request=None):
        """Send email notification for new plan requests"""
        try:
            from gym.models import EmailNotificationSettings
            
            # Determine notification type based on plan type
            notification_type = 'workout_plan_request' if plan_request.plan_type == 'workout' else 'diet_plan_request'
            
            # Get all admin emails that want this type of notification
            admin_emails = EmailNotificationSettings.get_active_notification_emails(notification_type)
            
            if not admin_emails:
                logger.info(f"No admin emails configured for {notification_type} notifications")
                return False
            
            # Get user's body information if available
            body_info = None
            try:
                body_info = plan_request.user.userprofile.body_information
            except Exception:
                pass
            
            # Prepare email context
            base_url = EmailNotificationService.get_base_url(request)
            context = {
                'plan_request': plan_request,
                'body_info': body_info,
                'plan_detail_url': f"{base_url}/plan-requests/{plan_request.id}/detail/",
                'approve_url': f"{base_url}/plan-requests/{plan_request.id}/update/?status=approved",
                'reject_url': f"{base_url}/plan-requests/{plan_request.id}/update/?status=rejected",
                'site_name': 'شیرنشان اسپورت',
                'current_date': timezone.now(),
            }
            
            # Add create plan URL if approved
            if plan_request.status == 'approved':
                if plan_request.plan_type == 'workout':
                    context['create_plan_url'] = f"{base_url}/add-workout-plan/?user_id={plan_request.user.id}"
                else:
                    context['create_plan_url'] = f"{base_url}/add-diet-plan/?user_id={plan_request.user.id}"
            
            # Render email template
            html_content = render_to_string('gym/emails/plan_request_notification.html', context)
            text_content = strip_tags(html_content)
            
            # Create subject based on plan type
            plan_type_display = plan_request.get_plan_type_display()
            subject = f"درخواست {plan_type_display} جدید - {plan_request.user.username}"
            
            # Send email to each admin
            for admin_email in admin_emails:
                try:
                    email = EmailMultiAlternatives(
                        subject=subject,
                        body=text_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[admin_email],
                    )
                    email.attach_alternative(html_content, "text/html")
                    email.send()
                    
                    logger.info(f"Plan request notification sent to {admin_email} for request {plan_request.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send plan request notification to {admin_email}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending plan request notification: {str(e)}")
            return False
    
    @staticmethod
    def send_payment_upload_notification(payment, request=None):
        """Send email notification for new payment uploads"""
        try:
            from gym.models import EmailNotificationSettings
            
            # Get all admin emails that want payment upload notifications
            admin_emails = EmailNotificationSettings.get_active_notification_emails('payment_upload')
            
            if not admin_emails:
                logger.info("No admin emails configured for payment upload notifications")
                return False
            
            # Prepare simple email content
            base_url = EmailNotificationService.get_base_url(request)
            subject = f"رسید پرداخت جدید - {payment.user.username}"
            
            message = f"""
            رسید پرداخت جدیدی توسط کاربر {payment.user.username} آپلود شده است.
            
            نوع پرداخت: {payment.get_payment_type_display()}
            مبلغ: {payment.amount:,} تومان
            تاریخ: {payment.payment_date.strftime('%Y/%m/%d %H:%M')}
            
            برای بررسی و تایید رسید، به پنل ادمین مراجعه کنید:
            {base_url}/payments/
            """
            
            # Send email to each admin
            for admin_email in admin_emails:
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin_email],
                        fail_silently=False,
                    )
                    
                    logger.info(f"Payment upload notification sent to {admin_email} for payment {payment.id}")
                    
                except Exception as e:
                    logger.error(f"Failed to send payment upload notification to {admin_email}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending payment upload notification: {str(e)}")
            return False
    
    @staticmethod
    def send_order_status_change_notification(order, old_status, new_status, request=None):
        """Send email notification when order status changes"""
        try:
            from gym.models import EmailNotificationSettings
            
            # Get all admin emails that want order status change notifications
            admin_emails = EmailNotificationSettings.get_active_notification_emails('shop_order')
            
            if not admin_emails:
                return False
            
            # Only send for important status changes
            important_statuses = ['paid', 'shipped', 'delivered', 'cancelled', 'returned']
            if new_status not in important_statuses:
                return False
            
            base_url = EmailNotificationService.get_base_url(request)
            subject = f"تغییر وضعیت سفارش {order.order_number}"
            
            message = f"""
            وضعیت سفارش {order.order_number} تغییر کرده است.
            
            مشتری: {order.first_name} {order.last_name}
            وضعیت قبلی: {dict(order.ORDER_STATUS).get(old_status, old_status)}
            وضعیت جدید: {dict(order.ORDER_STATUS).get(new_status, new_status)}
            
            مشاهده سفارش:
            {base_url}/admin/gym_shop/order/{order.id}/change/
            """
            
            # Send email to each admin
            for admin_email in admin_emails:
                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[admin_email],
                        fail_silently=False,
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to send order status change notification to {admin_email}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending order status change notification: {str(e)}")
            return False
    
    @staticmethod
    def test_email_configuration():
        """Test email configuration by sending a test email"""
        try:
            test_subject = "تست اطلاع‌رسانی ایمیل"
            test_message = """
            این ایمیل برای تست سیستم اطلاع‌رسانی ارسال شده است.
            
            اگر این ایمیل را دریافت کرده‌اید، یعنی تنظیمات ایمیل شما صحیح است.
            
            سیستم مدیریت شیرنشان اسپورت
            """
            
            # Send test email to DEFAULT_FROM_EMAIL
            send_mail(
                subject=test_subject,
                message=test_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
            
            logger.info("Test email sent successfully")
            return True
            
        except Exception as e:
            logger.error(f"Test email failed: {str(e)}")
            return False
    
    @staticmethod
    def create_default_notification_settings(admin_user):
        """Create default email notification settings for an admin user"""
        try:
            from gym.models import EmailNotificationSettings
            
            settings_obj, created = EmailNotificationSettings.objects.get_or_create(
                admin_user=admin_user,
                defaults={
                    'notification_email': admin_user.email or 'admin@example.com',
                    'notify_shop_orders': True,
                    'notify_workout_plan_requests': True,
                    'notify_diet_plan_requests': True,
                    'notify_payment_uploads': True,
                    'notification_frequency': 'immediate',
                    'is_active': True,
                }
            )
            
            return settings_obj
            
        except Exception as e:
            logger.error(f"Error creating default notification settings: {str(e)}")
            return None


# Convenience functions for easy import
def send_shop_order_notification(order, request=None):
    """Send shop order notification email"""
    return EmailNotificationService.send_shop_order_notification(order, request)

def send_plan_request_notification(plan_request, request=None):
    """Send plan request notification email"""
    return EmailNotificationService.send_plan_request_notification(plan_request, request)

def send_payment_upload_notification(payment, request=None):
    """Send payment upload notification email"""
    return EmailNotificationService.send_payment_upload_notification(payment, request)

def send_order_status_change_notification(order, old_status, new_status, request=None):
    """Send order status change notification email"""
    return EmailNotificationService.send_order_status_change_notification(order, old_status, new_status, request)

def test_email_configuration():
    """Test email configuration"""
    return EmailNotificationService.test_email_configuration() 