"""
Evaluate the trained ML model and produce a presentable report.

Generates:
    1. Terminal output  – formatted metrics table, confusion matrix, feature chart
    2. JSON file        – saved_models/evaluation_report.json
    3. Text file        – saved_models/evaluation_report.txt  (printable)

Usage
-----
    python manage.py evaluate_model
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand

REPORT_DIR = Path(__file__).resolve().parent.parent.parent / 'saved_models'


class Command(BaseCommand):
    help = 'Evaluate the trained ML model and produce a presentable report'

    def handle(self, *args, **options):
        report_path = REPORT_DIR / 'training_report.json'

        if not report_path.exists():
            self.stderr.write(self.style.ERROR(
                '\n  No trained model found. Run  python manage.py train_fit_model  first.\n'
            ))
            sys.exit(1)

        with open(report_path) as f:
            report = json.load(f)

        lines = self._build_report(report)

        # ── Print to terminal ─────────────────────────────────────
        for line in lines:
            self.stdout.write(line)

        # ── Save text report ──────────────────────────────────────
        txt_path = REPORT_DIR / 'evaluation_report.txt'
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        self.stdout.write(self.style.SUCCESS(f'\n  Report saved → {txt_path}'))

        # ── Save JSON report ──────────────────────────────────────
        json_path = REPORT_DIR / 'evaluation_report.json'
        self._save_json(report, json_path)
        self.stdout.write(self.style.SUCCESS(f'  JSON   saved → {json_path}\n'))

    def _build_report(self, report):
        """Build a list of formatted lines for the evaluation report."""
        m = report.get('metrics', report.get('model_results', {}))
        # Handle old multi-model format gracefully
        if 'accuracy' not in m:
            best = report.get('best_model', '')
            m = report.get('model_results', {}).get(best, m)

        ds = report.get('dataset', {})
        cm = report.get('confusion_matrix', [[0, 0], [0, 0]])
        fi = report.get('feature_importance', {})
        model_name = report.get('model_name', report.get('best_model', 'Random Forest'))

        L = []
        W = 64

        L.append('')
        L.append('=' * W)
        L.append('  JOB-CANDIDATE FIT PREDICTION — MODEL EVALUATION REPORT')
        L.append('=' * W)
        L.append(f'  Date           : {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        L.append(f'  Algorithm      : {model_name}')
        L.append(f'  Training Time  : {report.get("training_time_seconds", "N/A")}s')
        L.append('')

        # ── Dataset ───────────────────────────────────────────────
        L.append('-' * W)
        L.append('  DATASET SUMMARY')
        L.append('-' * W)
        L.append(f'  Real samples       : {ds.get("n_real_samples", 0)}')
        L.append(f'  Synthetic samples  : {ds.get("n_synthetic_samples", 0)}')
        L.append(f'  Total samples      : {ds.get("n_total_samples", 0)}')
        pos = ds.get("positive_ratio", 0)
        L.append(f'  Class balance      : {pos:.1%} positive / {1 - pos:.1%} negative')
        L.append(f'  Train/Test split   : 80% / 20%')
        L.append(f'  Feature count      : {len(report.get("feature_names", []))}')
        L.append('')

        # ── Metrics ───────────────────────────────────────────────
        L.append('-' * W)
        L.append('  MODEL PERFORMANCE METRICS')
        L.append('-' * W)
        L.append(f'  {"Metric":<24} {"Score":>10}')
        L.append(f'  {"─" * 36}')
        L.append(f'  {"Accuracy":<24} {m.get("accuracy", 0):>10.4f}')
        L.append(f'  {"Precision":<24} {m.get("precision", 0):>10.4f}')
        L.append(f'  {"Recall":<24} {m.get("recall", 0):>10.4f}')
        L.append(f'  {"F1-Score":<24} {m.get("f1_score", 0):>10.4f}')
        L.append(f'  {"AUC-ROC":<24} {m.get("roc_auc", 0):>10.4f}')
        cv = m.get("cv_f1_mean", 0)
        cv_std = m.get("cv_f1_std", 0)
        L.append(f'  {"Cross-Val F1 (5-fold)":<24} {cv:.4f} +/- {cv_std:.4f}')
        L.append('')

        # ── Confusion Matrix ──────────────────────────────────────
        L.append('-' * W)
        L.append('  CONFUSION MATRIX')
        L.append('-' * W)
        L.append(f'                          Predicted')
        L.append(f'                     Not Fit    Good Fit')
        if len(cm) >= 2:
            tn, fp = cm[0][0], cm[0][1]
            fn, tp = cm[1][0], cm[1][1]
            L.append(f'  Actual Not Fit      {tn:>5}       {fp:>5}    (TN / FP)')
            L.append(f'  Actual Good Fit     {fn:>5}       {tp:>5}    (FN / TP)')
            total = tn + fp + fn + tp
            if total > 0:
                L.append(f'')
                L.append(f'  True Negatives  (TN) : {tn:>4}  — Correctly identified as NOT a good fit')
                L.append(f'  True Positives  (TP) : {tp:>4}  — Correctly identified as a GOOD fit')
                L.append(f'  False Positives (FP) : {fp:>4}  — Incorrectly predicted as good fit')
                L.append(f'  False Negatives (FN) : {fn:>4}  — Missed good candidates')
        L.append('')

        # ── Feature Importance ────────────────────────────────────
        L.append('-' * W)
        L.append('  FEATURE IMPORTANCE (Top 15)')
        L.append('-' * W)
        L.append(f'  {"Rank":<6} {"Feature":<28} {"Score":>8}  {"Visual"}')
        L.append(f'  {"─" * 56}')
        for i, (feat, imp) in enumerate(fi.items()):
            if i >= 15:
                break
            bar = '█' * int(imp * 100)
            L.append(f'  {i + 1:<6} {feat:<28} {imp:>8.4f}  {bar}')
        L.append('')

        # ── Interpretation ────────────────────────────────────────
        L.append('-' * W)
        L.append('  INTERPRETATION')
        L.append('-' * W)
        top_features = list(fi.keys())[:3]
        L.append(f'  The model relies most heavily on:')
        for i, f in enumerate(top_features, 1):
            L.append(f'    {i}. {f}')
        L.append('')
        acc = m.get("accuracy", 0)
        if acc >= 0.8:
            L.append('  Overall: The model shows STRONG predictive ability.')
        elif acc >= 0.65:
            L.append('  Overall: The model shows GOOD predictive ability.')
        else:
            L.append('  Overall: The model shows MODERATE predictive ability.')
            L.append('  Performance will improve as more real application data is collected.')
        L.append('')

        # ── What the model does ───────────────────────────────────
        L.append('-' * W)
        L.append('  WHAT THIS MODEL DOES')
        L.append('-' * W)
        L.append('  Input  : A (Job Seeker, Job Posting) pair')
        L.append('  Output : Probability (0.0 – 1.0) that the candidate is a good fit')
        L.append('  Method : 200 Decision Trees vote independently; majority wins')
        L.append('  Uses   : 23 features covering skills, experience, education,')
        L.append('           profile richness, assessment scores, and text similarity')
        L.append('')

        L.append('=' * W)
        L.append('  END OF EVALUATION REPORT')
        L.append('=' * W)
        L.append('')
        return L

    def _save_json(self, report, path):
        m = report.get('metrics', {})
        if 'accuracy' not in m:
            best = report.get('best_model', '')
            m = report.get('model_results', {}).get(best, m)

        doc = {
            'report_date': datetime.now().isoformat(),
            'model_name': report.get('model_name', report.get('best_model', 'Random Forest')),
            'dataset': report.get('dataset', {}),
            'metrics': {
                'accuracy': m.get('accuracy'),
                'precision': m.get('precision'),
                'recall': m.get('recall'),
                'f1_score': m.get('f1_score'),
                'auc_roc': m.get('roc_auc'),
                'cross_validation_f1': m.get('cv_f1_mean'),
            },
            'confusion_matrix': {
                'true_negative': report.get('confusion_matrix', [[0]])[0][0],
                'false_positive': report.get('confusion_matrix', [[0, 0]])[0][1],
                'false_negative': report.get('confusion_matrix', [[0, 0], [0]])[1][0],
                'true_positive': report.get('confusion_matrix', [[0, 0], [0, 0]])[1][1],
            },
            'feature_importance': report.get('feature_importance', {}),
            'training_time_seconds': report.get('training_time_seconds'),
        }
        with open(path, 'w') as f:
            json.dump(doc, f, indent=2)
