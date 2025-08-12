"""
Django management command to train the anomaly detection model
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from flights.ml_pipeline import AnomalyDetectionModel, AnomalyDetectionPipeline
from flights.models import Flight
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train the flight anomaly detection model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contamination',
            type=float,
            default=0.1,
            help='Expected proportion of outliers in the data (default: 0.1)'
        )
        parser.add_argument(
            '--save-model',
            action='store_true',
            help='Save the trained model to disk'
        )
        parser.add_argument(
            '--run-detection',
            action='store_true',
            help='Run anomaly detection on all flights after training'
        )
        parser.add_argument(
            '--flight-limit',
            type=int,
            help='Limit the number of flights used for training (for testing)'
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Starting anomaly detection model training...')
        
        start_time = timezone.now()
        
        try:
            # Check if we have flight data
            flight_count = Flight.objects.count()
            if flight_count == 0:
                raise CommandError('❌ No flight data available. Please import some flights first.')
            
            self.stdout.write(f'📊 Found {flight_count} flight records in database')
            
            # Prepare queryset
            flights_queryset = Flight.objects.all()
            if options['flight_limit']:
                flights_queryset = flights_queryset[:options['flight_limit']]
                self.stdout.write(f'🔬 Limited to {options["flight_limit"]} flights for training')
            
            # Initialize model
            model = AnomalyDetectionModel(contamination=options['contamination'])
            self.stdout.write(f'🧠 Initialized model with contamination={options["contamination"]}')
            
            # Train model
            self.stdout.write('⚙️  Training model...')
            training_results = model.train(flights_queryset)
            
            if not training_results['success']:
                raise CommandError(f'❌ Model training failed: {training_results.get("error", "Unknown error")}')
            
            # Display training results
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Model training completed successfully!\n'
                    f'   📈 Training samples: {training_results["training_samples"]}\n'
                    f'   🔍 Features count: {training_results["features_count"]}\n'
                    f'   📊 Cross-validation AUC: {training_results["cv_auc_mean"]:.3f} ± {training_results["cv_auc_std"]:.3f}\n'
                    f'   ⏱️  Training time: {training_results["training_time_seconds"]:.2f} seconds'
                )
            )
            
            # Save model if requested
            if options['save_model']:
                self.stdout.write('💾 Saving model to disk...')
                model_path = model.save_model()
                self.stdout.write(self.style.SUCCESS(f'✅ Model saved to: {model_path}'))
            
            # Run detection if requested
            if options['run_detection']:
                self.stdout.write('🔍 Running anomaly detection on all flights...')
                pipeline = AnomalyDetectionPipeline(model)
                detection_results = pipeline.run_full_pipeline(retrain=False)
                
                if detection_results['success']:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Anomaly detection completed!\n'
                            f'   ✈️  Flights processed: {detection_results["total_flights_processed"]}\n'
                            f'   🚨 Anomalies detected: {detection_results["total_anomalies_detected"]}\n'
                            f'   ⏱️  Total time: {detection_results["total_processing_time_seconds"]:.2f} seconds'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Anomaly detection failed: {detection_results.get("error", "Unknown error")}')
                    )
            
            total_time = (timezone.now() - start_time).total_seconds()
            self.stdout.write(
                self.style.SUCCESS(f'🎉 Command completed in {total_time:.2f} seconds')
            )
            
        except Exception as e:
            logger.error(f"Model training command failed: {str(e)}", exc_info=True)
            raise CommandError(f'❌ Command failed: {str(e)}')