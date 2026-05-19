from django.core.management.base import BaseCommand

from api.services.lost_pet_service import backfill_lost_reports_for_lost_pets


class Command(BaseCommand):
    help = "Backfill active lost pet reports for pets already marked as lost."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Persist changes. Without this flag the command only previews.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit the number of lost pets processed.",
        )

    def handle(self, *args, **options):
        commit = options["commit"]
        limit = options["limit"]
        results = backfill_lost_reports_for_lost_pets(commit=commit, limit=limit)

        mode = "COMMIT" if commit else "DRY RUN"
        self.stdout.write(self.style.WARNING(f"{mode}: processed {len(results)} lost pets"))

        for result in results:
            self.stdout.write(
                " - {action}: {pet_name} ({pet_id}) report={report_id} owner={owner_id} location={location}".format(
                    action=result.get("action"),
                    pet_name=result.get("pet_name"),
                    pet_id=result.get("pet_id"),
                    report_id=result.get("report_id") or "-",
                    owner_id=result.get("owner_id") or "-",
                    location=result.get("last_seen_location") or "-",
                )
            )

