from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("system", "0021_operatortrainingbooking_company_name"),
    ]

    operations = [
        migrations.AddField(
            model_name="scheduleslot",
            name="prerequisite",
            field=models.TextField(
                blank=True,
                help_text="Optional prerequisite shown on the booking form",
            ),
        ),
    ]