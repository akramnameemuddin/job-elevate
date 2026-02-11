"""
Management command to train the Job-Candidate Fit ML model.

Usage
-----
    python manage.py train_fit_model
    python manage.py train_fit_model --synthetic 1000
"""

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Train the Job-Candidate Fit Prediction ML model (Random Forest)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--synthetic', type=int, default=500,
            help='Number of synthetic training samples to generate (default: 500)',
        )
        parser.add_argument(
            '--min-samples', type=int, default=100,
            help='Minimum total samples required for training (default: 100)',
        )

    def handle(self, *args, **options):
        from ml.trainer import train_and_evaluate

        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING(
            '  Job-Candidate Fit Model — Random Forest Training'
        ))
        self.stdout.write('=' * 60)

        try:
            report = train_and_evaluate(
                min_samples=options['min_samples'],
                synthetic_count=options['synthetic'],
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f'\n  Training failed: {exc}'))
            import traceback
            traceback.print_exc()
            sys.exit(1)

        # ── Dataset summary ───────────────────────────────────────
        ds = report['dataset']
        self.stdout.write(self.style.SUCCESS('\n  Dataset'))
        self.stdout.write(f'    Real samples:      {ds["n_real_samples"]}')
        self.stdout.write(f'    Synthetic samples: {ds["n_synthetic_samples"]}')
        self.stdout.write(f'    Total:             {ds["n_total_samples"]}')
        self.stdout.write(f'    Positive ratio:    {ds["positive_ratio"]:.2%}')

        # ── Model metrics ─────────────────────────────────────────
        m = report['metrics']
        self.stdout.write(self.style.SUCCESS(f'\n  Random Forest (200 trees) — Test-Set Metrics'))
        self.stdout.write(f'    {"Metric":<20} {"Value":>10}')
        self.stdout.write(f'    {"-" * 32}')
        self.stdout.write(f'    {"Accuracy":<20} {m["accuracy"]:>10.4f}')
        self.stdout.write(f'    {"Precision":<20} {m["precision"]:>10.4f}')
        self.stdout.write(f'    {"Recall":<20} {m["recall"]:>10.4f}')
        self.stdout.write(f'    {"F1-Score":<20} {m["f1_score"]:>10.4f}')
        self.stdout.write(f'    {"AUC-ROC":<20} {m["roc_auc"]:>10.4f}')
        self.stdout.write(f'    {"CV F1 (5-fold)":<20} {m["cv_f1_mean"]:.4f} +/- {m["cv_f1_std"]:.3f}')

        # ── Confusion matrix ──────────────────────────────────────
        cm = report['confusion_matrix']
        self.stdout.write(self.style.SUCCESS('\n  Confusion Matrix'))
        self.stdout.write(f'                     Predicted')
        self.stdout.write(f'                  Not Fit   Good Fit')
        self.stdout.write(f'    Actual Not Fit  {cm[0][0]:>5}     {cm[0][1]:>5}')
        self.stdout.write(f'    Actual Good Fit {cm[1][0]:>5}     {cm[1][1]:>5}')

        # ── Feature importance ────────────────────────────────────
        self.stdout.write(self.style.SUCCESS('\n  Top-10 Feature Importances'))
        for i, (feat, imp) in enumerate(report['feature_importance'].items()):
            if i >= 10:
                break
            bar = '#' * int(imp * 120)
            self.stdout.write(f'    {feat:<28} {imp:.4f}  {bar}')

        # ── Summary ───────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'  Model: Random Forest  |  F1 = {m["f1_score"]:.4f}  |  AUC = {m["roc_auc"]:.4f}'
        ))
        self.stdout.write(f'  Saved to   : {report["model_path"]}')
        self.stdout.write(f'  Report     : {report["model_path"].replace("job_fit_model.joblib", "training_report.json")}')
        self.stdout.write(f'  Time       : {report["training_time_seconds"]:.1f}s')
        self.stdout.write('')
