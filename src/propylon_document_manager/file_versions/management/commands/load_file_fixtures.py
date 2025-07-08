from django.core.management.base import BaseCommand, CommandError
from propylon_document_manager.file_versions.models import FileVersion

file_versions = [
    'bill_document',
    'amendment_document',
    'act_document',
    'statute_document',
]

class Command(BaseCommand):
    help = "Load basic file version fixtures"

    def handle(self, *args, **options):
        for file_name in file_versions:
            FileVersion.objects.create(
                file_name=file_name,
                version_number=1
            )

        self.stdout.write(
            self.style.SUCCESS('Successfully created %s file versions' % len(file_versions))
        )
