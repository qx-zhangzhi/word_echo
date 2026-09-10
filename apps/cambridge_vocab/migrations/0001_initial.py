import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CambridgeVocabEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("skill", models.CharField(choices=[("listening", "听力"), ("reading", "阅读")], max_length=20)),
                ("entry_type", models.CharField(choices=[("unknown", "不认识的词"), ("answer", "答案词"), ("synonym", "同义替换")], default="unknown", max_length=20)),
                ("word", models.CharField(max_length=120)),
                ("meaning_cn", models.CharField(blank=True, max_length=255)),
                ("synonym_replacements", models.TextField(blank=True)),
                ("original_expression", models.CharField(blank=True, max_length=255)),
                ("example_sentence", models.TextField(blank=True)),
                ("note", models.TextField(blank=True)),
                ("book", models.CharField(blank=True, max_length=40)),
                ("test", models.CharField(blank=True, max_length=40)),
                ("section_or_passage", models.CharField(blank=True, max_length=80)),
                ("question_numbers", models.CharField(blank=True, max_length=80)),
                ("source_title", models.CharField(blank=True, max_length=255)),
                ("source_detail", models.TextField(blank=True)),
                ("is_learned", models.BooleanField(default=False)),
                ("learned_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["is_learned", "-created_at", "word"],
            },
        ),
        migrations.AddIndex(
            model_name="cambridgevocabentry",
            index=models.Index(fields=["user", "skill", "entry_type"], name="cambridge_v_user_id_77f690_idx"),
        ),
        migrations.AddIndex(
            model_name="cambridgevocabentry",
            index=models.Index(fields=["user", "is_learned", "learned_at"], name="cambridge_v_user_id_a0ec62_idx"),
        ),
        migrations.AddIndex(
            model_name="cambridgevocabentry",
            index=models.Index(fields=["book", "test", "question_numbers"], name="cambridge_v_book_1c72bf_idx"),
        ),
    ]
