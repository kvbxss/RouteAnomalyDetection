"""
Django management command to run anomaly detection on flights
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from flights.ml_pipeline import AnomalyDetectionModel, AnomalyDetectionPipeline
from flights.models import Flight, AnomalyDetection
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run anomaly detection on flight data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-path',
            type=str,
            help='Path to saved model file'
        )
        parser.add_argument(
            '--flight-ids',
            nargs='+',
            help='Specific flight IDs to process (space-separated)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing anomaly detection records before processing'
        )
        parser.add_argument(
            '--min-confidence',
            type=float,
            default=0.0,
            help='Minimum confidence threshold for reporting anomalies (default: 0.0)'
        )

    def handle(self, *args, **options):
        self.stdout.write('🔍 Starting anomaly detection...')
        
        start_time = timezone.now()
        
        try:
            # Check if we have flight data
            flight_count = Flight.objects.count()
            if flight_count == 0:
                raise CommandError('❌ No flight data available. Please import some flights first.')
            
            # Clear existing anomalies if requested
            if options['clear_existing']:
                existing_count = AnomalyDetection.objects.count()
                AnomalyDetection.objects.all().delete()
                self.stdout.write(f'🗑️  Cleared {existing_count} existing anomaly records')
            
            # Initialize model
            model = AnomalyDetectionModel()
            
            # Load model from file if specified
            if options['model_path']:
                if not os.path.exists(options['model_path']):
                    raise CommandError(f'❌ Model file not found: {options["model_path"]}')
                
                self.stdout.write(f'📂 Loading model from {options["model_path"]}')
                if not model.load_model(options['model_path']):
                    raise CommandError('❌ Failed to load model from file')
                self.stdout.write('✅ Model loaded successfully')
            else:
                # Train model if not loaded from file
                self.stdout.write('🧠 No model file specified, training new model...')
                training_results = model.train()
                
                if not training_results['success']:
                    raise CommandError(f'❌ Model training failed: {training_results.get("error", "Unknown error")}')
                
                self.stdout.write(f'✅ Model trained with {training_results["training_samples"]} samples')
            
            # Initialize pipeline
            pipeline = AnomalyDetectionPipeline(model)
            
            # Determine which flights to process
            if options['flight_ids']:
                flight_ids = options['flight_ids']
                self.stdout.write(f'🎯 Processing specific flights: {flight_ids}')
                
                # Process the specified flights
                results = pipeline.process_flight_batch(flight_ids)
            else:
                self.stdout.write('🌍 Processing all flights...')
                
                # Run full pipeline
                results = pipeline.run_full_pipeline(retrain=False)
            
            # Display results
            if results['success']:
                if 'total_flights_processed' in results:
                    # Full pipeline results
                    flights_processed = results['total_flights_processed']
                    anomalies_detected = results['total_anomalies_detected']
                else:
                    # Batch processing results
                    flights_processed = results['processed_flights']
                    anomalies_detected = results['anomalies_detected']
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Anomaly detection completed!\n'
                        f'   ✈️  Flights processed: {flights_processed}\n'
                        f'   🚨 Anomalies detected: {anomalies_detected}\n'
                        f'   ⏱️  Processing time: {results.get("processing_time_seconds", results.get("total_processing_time_seconds", 0)):.2f} seconds'
                    )
                )
                
                # Show high-confidence anomalies if any
                high_confidence_anomalies = AnomalyDetection.objects.filter(
                    confidence_score__gte=options['min_confidence']
                ).order_by('-confidence_score')[:10]
                
                if high_confidence_anomalies.exists():
                    self.stdout.write(f'\n🔥 Top anomalies (confidence >= {options["min_confidence"]:.2f}):')
                    for anomaly in high_confidence_anomalies:
                        self.stdout.write(
                            f'  • {anomaly.flight.flight_id} ({anomaly.anomaly_type}): '
                            f'{anomaly.confidence_score:.3f} confidence'
                        )
            else:
                error_msg = results.get('error', 'Unknown error')
                if 'errors' in results and results['errors']:
                    error_msg = '; '.join(results['errors'])
                raise CommandError(f'❌ Anomaly detection failed: {error_msg}')
            
            total_time = (timezone.now() - start_time).total_seconds()
            self.stdout.write(
                self.style.SUCCESS(f'🎉 Command completed in {total_time:.2f} seconds')
            )
            
        except Exception as e:
            logger.error(f"Anomaly detection command failed: {str(e)}", exc_info=True)
            raise CommandError(f'❌ Command failed: {str(e)}')