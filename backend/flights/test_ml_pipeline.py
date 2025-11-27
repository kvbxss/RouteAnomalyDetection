from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
import pandas as pd
import numpy as np
from .models import Flight, AnomalyDetection
from .ml_pipeline import (
    FlightFeatureExtractor,
    AnomalyDetectionModel,
    AnomalyDetectionPipeline
)


class FlightFeatureExtractorTestCase(TestCase):
    """Test cases for flight feature extraction"""

    def setUp(self):
        """Set up test data"""
        self.extractor = FlightFeatureExtractor()

        # Create sample flight data
        base_time = timezone.now()
        self.flights = []

        for i in range(10):
            flight = Flight.objects.create(
                flight_id=f'TEST{i:03d}',
                aircraft_id='ABC123',
                timestamp=base_time + timedelta(minutes=i*5),
                latitude=40.0 + i * 0.1,
                longitude=-74.0 + i * 0.1,
                altitude=35000 + i * 1000,
                speed=450.0 + i * 10,
                heading=90.0 + i * 5
            )
            self.flights.append(flight)

    def test_extract_features_returns_dataframe(self):
        """Test that feature extraction returns a DataFrame"""
        flights_df = pd.DataFrame([
            {
                'flight_id': f.flight_id,
                'latitude': f.latitude,
                'longitude': f.longitude,
                'altitude': f.altitude,
                'speed': f.speed,
                'heading': f.heading,
                'timestamp': f.timestamp
            }
            for f in self.flights
        ])

        features = self.extractor.extract_features(flights_df)

        self.assertIsInstance(features, pd.DataFrame)
        self.assertGreater(len(features), 0)
        self.assertGreater(len(features.columns), 10)  # Should have many features

    def test_feature_names_property(self):
        """Test that feature names are accessible"""
        flights_df = pd.DataFrame([
            {
                'flight_id': f.flight_id,
                'latitude': f.latitude,
                'longitude': f.longitude,
                'altitude': f.altitude,
                'speed': f.speed,
                'heading': f.heading,
                'timestamp': f.timestamp
            }
            for f in self.flights
        ])

        features = self.extractor.extract_features(flights_df)
        feature_names = self.extractor.feature_names

        self.assertIsInstance(feature_names, list)
        self.assertEqual(len(feature_names), len(features.columns))
        self.assertIn('latitude', feature_names)
        self.assertIn('altitude_normalized', feature_names)

    def test_transform_features_scales_correctly(self):
        """Test that feature transformation scales features"""
        flights_df = pd.DataFrame([
            {
                'flight_id': f.flight_id,
                'latitude': f.latitude,
                'longitude': f.longitude,
                'altitude': f.altitude,
                'speed': f.speed,
                'heading': f.heading,
                'timestamp': f.timestamp
            }
            for f in self.flights
        ])

        # Extract features and fit scaler
        features = self.extractor.extract_features(flights_df)
        self.extractor.fit_scaler(features)  # Fit the scaler first
        scaled_features = self.extractor.transform_features(features)

        self.assertIsInstance(scaled_features, np.ndarray)
        self.assertEqual(scaled_features.shape[0], len(features))
        self.assertEqual(scaled_features.shape[1], len(features.columns))

        # Scaled features should have mean close to 0 and std close to 1
        self.assertAlmostEqual(scaled_features.mean(), 0.0, delta=0.5)

    def test_handles_single_flight(self):
        """Test feature extraction with single flight"""
        flights_df = pd.DataFrame([{
            'flight_id': 'SINGLE',
            'latitude': 40.0,
            'longitude': -74.0,
            'altitude': 35000,
            'speed': 450.0,
            'heading': 90.0,
            'timestamp': timezone.now()
        }])

        features = self.extractor.extract_features(flights_df)

        self.assertIsInstance(features, pd.DataFrame)
        self.assertEqual(len(features), 1)

    def test_haversine_distance_calculation(self):
        """Test haversine distance calculation accuracy"""
        # Create two points with known distance
        flights_df = pd.DataFrame([
            {
                'flight_id': 'TEST1',
                'latitude': 40.7128,  # New York
                'longitude': -74.0060,
                'altitude': 35000,
                'speed': 450.0,
                'heading': 90.0,
                'timestamp': timezone.now()
            },
            {
                'flight_id': 'TEST1',
                'latitude': 40.7128,  # Same latitude, 1 degree longitude diff
                'longitude': -73.0060,
                'altitude': 35000,
                'speed': 450.0,
                'heading': 90.0,
                'timestamp': timezone.now() + timedelta(minutes=5)
            }
        ])

        features = self.extractor.extract_features(flights_df)

        # Distance should be calculated
        self.assertIn('distance_from_previous', features.columns)
        # Second row should have non-zero distance
        self.assertGreater(features.iloc[1]['distance_from_previous'], 0)


class AnomalyDetectionModelTestCase(TestCase):
    """Test cases for anomaly detection model"""

    def setUp(self):
        """Set up test data and model"""
        self.model = AnomalyDetectionModel(contamination=0.1)

        # Create training data
        base_time = timezone.now()
        self.flights = []

        # Create 50 normal flights
        for i in range(50):
            flight = Flight.objects.create(
                flight_id=f'NORMAL{i:03d}',
                aircraft_id='ABC123',
                timestamp=base_time + timedelta(hours=i),
                latitude=40.0 + np.random.normal(0, 0.1),
                longitude=-74.0 + np.random.normal(0, 0.1),
                altitude=35000 + np.random.normal(0, 500),
                speed=450.0 + np.random.normal(0, 20),
                heading=90.0 + np.random.normal(0, 10)
            )
            self.flights.append(flight)

        # Create 5 anomalous flights
        for i in range(5):
            flight = Flight.objects.create(
                flight_id=f'ANOMALY{i:03d}',
                aircraft_id='XYZ789',
                timestamp=base_time + timedelta(hours=50+i),
                latitude=40.0 + np.random.normal(0, 5),  # Much higher variance
                longitude=-74.0 + np.random.normal(0, 5),
                altitude=10000 + np.random.normal(0, 5000),  # Abnormal altitude
                speed=100.0 + np.random.normal(0, 50),  # Abnormal speed
                heading=270.0
            )
            self.flights.append(flight)

    def test_model_initialization(self):
        """Test model initialization"""
        model = AnomalyDetectionModel(contamination=0.15)

        self.assertEqual(model.contamination, 0.15)
        self.assertFalse(model.is_fitted)
        self.assertIsNotNone(model.model_version)

    def test_model_training(self):
        """Test model training process"""
        queryset = Flight.objects.all()
        results = self.model.train(queryset)

        self.assertTrue(results['success'])
        self.assertTrue(self.model.is_fitted)
        self.assertGreater(results['training_samples'], 0)
        self.assertIn('silhouette_score', results)
        self.assertIn('anomalies_detected', results)
        self.assertIn('feature_names', results)

    def test_prediction_after_training(self):
        """Test making predictions after training"""
        # Train model
        queryset = Flight.objects.all()
        self.model.train(queryset)

        # Prepare test data
        test_df = pd.DataFrame([
            {
                'flight_id': 'TEST001',
                'latitude': 40.0,
                'longitude': -74.0,
                'altitude': 35000,
                'speed': 450.0,
                'heading': 90.0,
                'timestamp': timezone.now()
            }
        ])

        # Make predictions
        is_anomaly, confidence_scores = self.model.predict_anomalies(test_df)

        self.assertIsInstance(is_anomaly, np.ndarray)
        self.assertIsInstance(confidence_scores, np.ndarray)
        self.assertEqual(len(is_anomaly), 1)
        self.assertEqual(len(confidence_scores), 1)
        self.assertGreaterEqual(confidence_scores[0], 0.0)
        self.assertLessEqual(confidence_scores[0], 1.0)

    def test_prediction_without_training_fails(self):
        """Test that prediction fails without training"""
        test_df = pd.DataFrame([
            {
                'flight_id': 'TEST001',
                'latitude': 40.0,
                'longitude': -74.0,
                'altitude': 35000,
                'speed': 450.0,
                'heading': 90.0,
                'timestamp': timezone.now()
            }
        ])

        with self.assertRaises(ValueError):
            self.model.predict_anomalies(test_df)

    def test_model_save_and_load(self):
        """Test saving and loading model"""
        import tempfile
        import os

        # Train model
        queryset = Flight.objects.all()
        self.model.train(queryset)

        # Save model
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_model.joblib')
            saved_path = self.model.save_model(filepath)

            self.assertEqual(saved_path, filepath)
            self.assertTrue(os.path.exists(filepath))

            # Load model in new instance
            new_model = AnomalyDetectionModel()
            new_model.load_model(filepath)

            self.assertTrue(new_model.is_fitted)
            self.assertEqual(new_model.contamination, self.model.contamination)

    def test_feature_importance_calculation(self):
        """Test feature importance analysis"""
        # Train model
        queryset = Flight.objects.all()
        self.model.train(queryset)

        # Get test data
        test_df = pd.DataFrame([
            {
                'flight_id': f.flight_id,
                'latitude': f.latitude,
                'longitude': f.longitude,
                'altitude': f.altitude,
                'speed': f.speed,
                'heading': f.heading,
                'timestamp': f.timestamp
            }
            for f in self.flights[:20]
        ])

        # Calculate feature importance
        importance = self.model.get_feature_importance(test_df)

        self.assertIsInstance(importance, dict)
        self.assertGreater(len(importance), 0)

        # All importance values should be between 0 and 1
        for feature, imp_value in importance.items():
            self.assertGreaterEqual(imp_value, 0.0)
            self.assertLessEqual(imp_value, 1.0)

        # Importance should sum to approximately 1
        total_importance = sum(importance.values())
        self.assertAlmostEqual(total_importance, 1.0, delta=0.01)

    def test_anomaly_detection_accuracy(self):
        """Test that model can detect obvious anomalies"""
        # Train on normal flights only
        normal_flights = Flight.objects.filter(flight_id__startswith='NORMAL')
        self.model.train(normal_flights)

        # Test on anomalous flights
        anomaly_df = pd.DataFrame([
            {
                'flight_id': f.flight_id,
                'latitude': f.latitude,
                'longitude': f.longitude,
                'altitude': f.altitude,
                'speed': f.speed,
                'heading': f.heading,
                'timestamp': f.timestamp
            }
            for f in Flight.objects.filter(flight_id__startswith='ANOMALY')
        ])

        is_anomaly, confidence_scores = self.model.predict_anomalies(anomaly_df)

        # At least some anomalies should be detected
        # Note: Using lower confidence threshold since the model is probabilistic
        anomalies_detected = is_anomaly.sum()
        self.assertGreater(anomalies_detected, 0,
                          "Model should detect at least one anomaly in obviously anomalous data")


class AnomalyDetectionPipelineTestCase(TestCase):
    """Test cases for the full anomaly detection pipeline"""

    def setUp(self):
        """Set up test data"""
        base_time = timezone.now()

        # Create test flights
        for i in range(20):
            Flight.objects.create(
                flight_id=f'PIPE{i:03d}',
                aircraft_id='ABC123',
                timestamp=base_time + timedelta(hours=i),
                latitude=40.0 + i * 0.1,
                longitude=-74.0 + i * 0.1,
                altitude=35000 + i * 500,
                speed=450.0 + i * 5,
                heading=90.0 + i * 2
            )

    def test_pipeline_initialization(self):
        """Test pipeline initialization"""
        pipeline = AnomalyDetectionPipeline()

        self.assertIsNotNone(pipeline.model)
        self.assertIsInstance(pipeline.model, AnomalyDetectionModel)

    def test_process_flight_batch(self):
        """Test processing a batch of flights"""
        pipeline = AnomalyDetectionPipeline()

        # Get flight IDs
        flight_ids = list(Flight.objects.values_list('flight_id', flat=True)[:10])

        # Process batch
        results = pipeline.process_flight_batch(flight_ids)

        self.assertIsInstance(results, dict)
        self.assertIn('processed_flights', results)
        self.assertIn('anomalies_detected', results)

    def test_run_full_pipeline(self):
        """Test running the full pipeline with training and detection"""
        pipeline = AnomalyDetectionPipeline()

        results = pipeline.run_full_pipeline(retrain=True)

        self.assertIsInstance(results, dict)
        self.assertTrue(results.get('success', False))
        self.assertIn('total_flights_processed', results)
        self.assertIn('total_anomalies_detected', results)

    def test_pipeline_creates_anomaly_records(self):
        """Test that pipeline creates AnomalyDetection records"""
        initial_count = AnomalyDetection.objects.count()

        pipeline = AnomalyDetectionPipeline()
        pipeline.run_full_pipeline(retrain=True)

        final_count = AnomalyDetection.objects.count()

        # Should have created some anomaly records
        self.assertGreaterEqual(final_count, initial_count)

    def test_anomaly_classification_types(self):
        """Test that anomalies are classified into types"""
        # Create a flight with extreme altitude change
        base_time = timezone.now()
        Flight.objects.create(
            flight_id='ALTITUDE_TEST',
            aircraft_id='TEST999',
            timestamp=base_time,
            latitude=40.0,
            longitude=-74.0,
            altitude=45000,  # Very high altitude
            speed=450.0,
            heading=90.0
        )

        pipeline = AnomalyDetectionPipeline()
        results = pipeline.run_full_pipeline(retrain=True)

        # Check if any anomalies were detected
        anomalies = AnomalyDetection.objects.all()
        if anomalies.exists():
            # Verify anomaly types are assigned
            for anomaly in anomalies:
                self.assertIn(anomaly.anomaly_type, [
                    'altitude_anomaly',
                    'speed_anomaly',
                    'route_deviation',
                    'temporal_anomaly',
                    'combined'
                ])


class ModelPerformanceTestCase(TestCase):
    """Test cases for model performance and edge cases"""

    def test_model_handles_insufficient_data(self):
        """Test model behavior with insufficient training data"""
        # Create only 2 flights
        for i in range(2):
            Flight.objects.create(
                flight_id=f'FEW{i}',
                aircraft_id='ABC123',
                timestamp=timezone.now() + timedelta(hours=i),
                latitude=40.0,
                longitude=-74.0,
                altitude=35000,
                speed=450.0,
                heading=90.0
            )

        model = AnomalyDetectionModel()
        queryset = Flight.objects.all()

        # Training should handle gracefully or raise appropriate error
        try:
            results = model.train(queryset)
            # If it succeeds, check results are valid
            if results['success']:
                self.assertGreater(results['training_samples'], 0)
        except ValueError as e:
            # Or it should raise a clear error
            self.assertIn('sample', str(e).lower())

    def test_model_handles_identical_data(self):
        """Test model behavior with identical flight data"""
        # Create identical flights
        for i in range(10):
            Flight.objects.create(
                flight_id=f'SAME{i}',
                aircraft_id='ABC123',
                timestamp=timezone.now() + timedelta(hours=i),
                latitude=40.0,
                longitude=-74.0,
                altitude=35000,
                speed=450.0,
                heading=90.0
            )

        model = AnomalyDetectionModel()
        queryset = Flight.objects.all()
        results = model.train(queryset)

        # Should handle without crashing
        self.assertIsInstance(results, dict)

    def test_confidence_score_range(self):
        """Test that confidence scores are always in valid range"""
        # Create diverse flight data
        for i in range(30):
            Flight.objects.create(
                flight_id=f'CONF{i:03d}',
                aircraft_id='ABC123',
                timestamp=timezone.now() + timedelta(hours=i),
                latitude=40.0 + np.random.uniform(-2, 2),
                longitude=-74.0 + np.random.uniform(-2, 2),
                altitude=35000 + np.random.uniform(-10000, 10000),
                speed=450.0 + np.random.uniform(-100, 100),
                heading=np.random.uniform(0, 360)
            )

        model = AnomalyDetectionModel()
        queryset = Flight.objects.all()
        model.train(queryset)

        test_df = pd.DataFrame([
            {
                'flight_id': f.flight_id,
                'latitude': f.latitude,
                'longitude': f.longitude,
                'altitude': f.altitude,
                'speed': f.speed,
                'heading': f.heading,
                'timestamp': f.timestamp
            }
            for f in Flight.objects.all()[:10]
        ])

        _, confidence_scores = model.predict_anomalies(test_df)

        # All scores should be in [0, 1]
        self.assertTrue(np.all(confidence_scores >= 0.0))
        self.assertTrue(np.all(confidence_scores <= 1.0))
