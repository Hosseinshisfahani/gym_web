from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('gym', '0005_merge_20250506_2237'),
    ]

    operations = [
        migrations.RunSQL(
            # Forward SQL
            """
            CREATE INDEX IF NOT EXISTS idx_userprofile_user ON gym_userprofile(user_id);
            CREATE INDEX IF NOT EXISTS idx_workoutplan_user ON gym_workoutplan(user_id);
            CREATE INDEX IF NOT EXISTS idx_dietplan_user ON gym_dietplan(user_id);
            CREATE INDEX IF NOT EXISTS idx_certificate_user ON gym_certificate(user_id);
            CREATE INDEX IF NOT EXISTS idx_attendance_userprofile ON gym_attendance(user_profile_id);
            CREATE INDEX IF NOT EXISTS idx_payment_user ON gym_payment(user_id);
            CREATE INDEX IF NOT EXISTS idx_ticket_user ON gym_ticket(user_id);
            CREATE INDEX IF NOT EXISTS idx_bookletpayment_user ON gym_bookletpayment(user_id);
            CREATE INDEX IF NOT EXISTS idx_planrequest_user ON gym_planrequest(user_id);
            """,
            # Reverse SQL
            """
            DROP INDEX IF EXISTS idx_userprofile_user;
            DROP INDEX IF EXISTS idx_workoutplan_user;
            DROP INDEX IF EXISTS idx_dietplan_user;
            DROP INDEX IF EXISTS idx_certificate_user;
            DROP INDEX IF EXISTS idx_attendance_userprofile;
            DROP INDEX IF EXISTS idx_payment_user;
            DROP INDEX IF EXISTS idx_ticket_user;
            DROP INDEX IF EXISTS idx_bookletpayment_user;
            DROP INDEX IF EXISTS idx_planrequest_user;
            """
        ),
    ] 