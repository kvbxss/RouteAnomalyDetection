"""
Machine Learning Pipeline for Flight Route Anomaly Detection

This module implements the core ML functionality for detecting anomalies in flight routes
using isolation forest and other unsupervised learning techniques.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import joblib
import logging
from django.utils import timezone
from django.conf import settings
import os

from .models import Flight, AnomalyDetection

logger = logging.getLogger(__name__)


class FlightFeatureExtractor:
    """Extract features from flight data for anomaly detection"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []
    
    def extract_features(self, flights_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from flight data for ML model
        
        Args:
            flights_df: DataFrame with flight data
            
        Returns:
            DataFrame with extracted features
        """
        features = pd.DataFrame(index=flights_df.index)
        
        # Basic positional features
        features['latitude'] = flights_df['latitude']
        features['longitude'] = flights_df['longitude']
        features['altitude'] = flights_df['altitude']
        features['speed'] = flights_df['speed']
        features['heading'] = flights_df['heading']
        
        # Derived features
        features['altitude_normalized'] = features['altitude'] / 45000  # Normalize to cruise altitude
        features['speed_normalized'] = features['speed'] / 500  # Normalize to typical cruise speed
        
        # Route deviation features
        if len(flights_df) > 1:
            features['distance_from_previous'] = self._calculate_distances(flights_df)
            features['speed_change'] = features['speed'].diff().fillna(0)
            features['altitude_change'] = features['altitude'].diff().fillna(0)
            features['heading_change'] = self._calculate_heading_changes(flights_df['heading'])
        else:
            features['distance_from_previous'] = 0
            features['speed_change'] = 0
            features['altitude_change'] = 0
            features['heading_change'] = 0
        
        # Temporal features
        if 'timestamp' in flights_df.columns:
            features['hour_of_day'] = pd.to_datetime(flights_df['timestamp']).dt.hour
            features['day_of_week'] = pd.to_datetime(flights_df['timestamp']).dt.dayofweek
            
            # Time-based anomalies
            features['time_delta'] = pd.to_datetime(flights_df['timestamp']).diff().dt.total_seconds().fillna(0)
        else:
            features['hour_of_day'] = 12  # Default to noon
            features['day_of_week'] = 1   # Default to Monday
            features['time_delta'] = 0
        
        # Statistical features for route analysis
        if len(flights_df) > 2:
            # Rolling statistics for local anomalies
            window_size = min(5, len(flights_df))
            features['altitude_rolling_std'] = features['altitude'].rolling(window=window_size, center=True).std().fillna(0)
            features['speed_rolling_std'] = features['speed'].rolling(window=window_size, center=True).std().fillna(0)
            features['distance_rolling_mean'] = features['distance_from_previous'].rolling(window=window_size, center=True).mean().fillna(0)
        else:
            features['altitude_rolling_std'] = 0
            features['speed_rolling_std'] = 0
            features['distance_rolling_mean'] = 0
        
        # Remove any infinite or NaN values
        features = features.replace([np.inf, -np.inf], 0).fillna(0)
        
        self.feature_names = list(features.columns)
        logger.debug(f"Extracted {len(self.feature_names)} features: {self.feature_names}")
        
        return features
    
    def _calculate_distances(self, flights_df: pd.DataFrame) -> pd.Series:
        """Calculate haversine distances between consecutive points"""
        distances = [0]  # First point has no previous point
        
        for i in range(1, len(flights_df)):
            lat1, lon1 = flights_df.iloc[i-1][['latitude', 'longitude']]
            lat2, lon2 = flights_df.iloc[i][['latitude', 'longitude']]
            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            distances.append(distance)
        
        return pd.Series(distances, index=flights_df.index)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate the great circle distance between two points on earth (in km)"""
        # Convert decimal degrees to radians
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arcsin(np.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r
    
    def _calculate_heading_changes(self, headings: pd.Series) -> pd.Series:
        """Calculate heading changes accounting for circular nature of headings"""
        changes = [0]  # First point has no previous point
        
        for i in range(1, len(headings)):
            h1, h2 = headings.iloc[i-1], headings.iloc[i]
            
            # Handle circular nature of headings (0-360 degrees)
            diff = h2 - h1
            if diff > 180:
                diff -= 360
            elif diff < -180:
                diff += 360
            
            changes.append(abs(diff))
        
        return pd.Series(changes, index=headings.index)
    
    def fit_scaler(self, features_df: pd.DataFrame):
        """Fit the feature scaler on training data"""
        self.scaler.fit(features_df)
        logger.info(f"Feature scaler fitted on {len(features_df)} samples")
    
    def transform_features(self, features_df: pd.DataFrame) -> np.ndarray:
        """Transform features using fitted scaler"""
        return self.scaler.transform(features_df)


class AnomalyDetectionModel:
    """Isolation Forest model for flight anomaly detection"""
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42):
        """
        Initialize the anomaly detection model
        
        Args:
            contamination: Expected proportion of outliers in the data
            random_state: Random state for reproducibility
        """
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1
        )
        self.is_fitted = False
        self.feature_extractor = FlightFeatureExtractor()
        self.model_version = "1.0.0"
        self.contamination = contamination
        
    def prepare_training_data(self, flights_queryset=None) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare training data from flight records
        
        Args:
            flights_queryset: Optional Django queryset of Flight objects
            
        Returns:
            Tuple of (flights_df, features_df)
        """
        if flights_queryset is None:
            flights_queryset = Flight.objects.all()
        
        # Convert to DataFrame
        flights_data = list(flights_queryset.values(
            'id', 'flight_id', 'aircraft_id', 'timestamp', 
            'latitude', 'longitude', 'altitude', 'speed', 'heading'
        ))
        
        if not flights_data:
            raise ValueError("No flight data available for training")
        
        flights_df = pd.DataFrame(flights_data)
        
        # Sort by flight_id and timestamp for proper sequence analysis
        flights_df = flights_df.sort_values(['flight_id', 'timestamp'])
        
        logger.info(f"Prepared training data: {len(flights_df)} flight records from {flights_df['flight_id'].nunique()} unique flights")
        
        # Extract features
        features_df = self.feature_extractor.extract_features(flights_df)
        
        return flights_df, features_df
    
    def train(self, flights_queryset=None) -> Dict[str, Any]:
        """
        Train the anomaly detection model
        
        Args:
            flights_queryset: Optional Django queryset of Flight objects
            
        Returns:
            Training results dictionary
        """
        logger.info("Starting anomaly detection model training")
        start_time = timezone.now()
        
        try:
            # Prepare data
            flights_df, features_df = self.prepare_training_data(flights_queryset)
            
            # Fit feature scaler
            self.feature_extractor.fit_scaler(features_df)
            
            # Transform features
            features_scaled = self.feature_extractor.transform_features(features_df)
            
            # Train the model
            self.model.fit(features_scaled)
            self.is_fitted = True
            
            # Evaluate model using cross-validation
            cv_scores = cross_val_score(self.model, features_scaled, cv=5, scoring='roc_auc', n_jobs=-1)
            
            training_time = (timezone.now() - start_time).total_seconds()
            
            results = {
                'success': True,
                'training_samples': len(features_df),
                'features_count': len(self.feature_extractor.feature_names),
                'feature_names': self.feature_extractor.feature_names,
                'cv_auc_mean': cv_scores.mean(),
                'cv_auc_std': cv_scores.std(),
                'contamination': self.contamination,
                'model_version': self.model_version,
                'training_time_seconds': training_time
            }
            
            logger.info(f"Model training completed successfully in {training_time:.2f}s. "
                       f"CV AUC: {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
            
            return results
            
        except Exception as e:
            error_msg = f"Model training failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'training_time_seconds': (timezone.now() - start_time).total_seconds()
            }
    
    def predict_anomalies(self, flights_df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies for flight data
        
        Args:
            flights_df: DataFrame with flight data
            
        Returns:
            Tuple of (anomaly_predictions, anomaly_scores)
        """
        if not self.is_fitted:
            raise ValueError("Model must be trained before making predictions")
        
        # Extract and transform features
        features_df = self.feature_extractor.extract_features(flights_df)
        features_scaled = self.feature_extractor.transform_features(features_df)
        
        # Make predictions
        anomaly_predictions = self.model.predict(features_scaled)  # -1 for anomaly, 1 for normal
        anomaly_scores = self.model.decision_function(features_scaled)  # Higher values = more normal
        
        # Convert predictions to boolean (True for anomaly)
        is_anomaly = anomaly_predictions == -1
        
        # Convert scores to confidence scores (0-1, higher = more anomalous)
        confidence_scores = 1 / (1 + np.exp(anomaly_scores))  # Sigmoid transformation
        
        return is_anomaly, confidence_scores
    
    def save_model(self, filepath: str = None):
        """Save the trained model to disk"""
        if not self.is_fitted:
            raise ValueError("Cannot save untrained model")
        
        if filepath is None:
            models_dir = os.path.join(settings.BASE_DIR, 'models')
            os.makedirs(models_dir, exist_ok=True)
            filepath = os.path.join(models_dir, f'anomaly_model_v{self.model_version}.joblib')
        
        model_data = {
            'model': self.model,
            'feature_extractor': self.feature_extractor,
            'model_version': self.model_version,
            'contamination': self.contamination,
            'is_fitted': self.is_fitted,
            'saved_at': timezone.now()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: str):
        """Load a trained model from disk"""
        try:
            model_data = joblib.load(filepath)
            
            self.model = model_data['model']
            self.feature_extractor = model_data['feature_extractor']
            self.model_version = model_data['model_version']
            self.contamination = model_data['contamination']
            self.is_fitted = model_data['is_fitted']
            
            logger.info(f"Model loaded from {filepath} (version: {self.model_version})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model from {filepath}: {str(e)}")
            return False


class AnomalyDetectionPipeline:
    """Complete pipeline for flight anomaly detection"""
    
    def __init__(self, model: AnomalyDetectionModel = None):
        """
        Initialize the detection pipeline
        
        Args:
            model: Optional pre-trained model instance
        """
        self.model = model or AnomalyDetectionModel()
        self.logger = logging.getLogger(__name__)
    
    def process_flight_batch(self, flight_ids: List[str]) -> Dict[str, Any]:
        """
        Process a batch of flights for anomaly detection
        
        Args:
            flight_ids: List of flight IDs to process
            
        Returns:
            Processing results dictionary
        """
        start_time = timezone.now()
        results = {
            'success': False,
            'processed_flights': 0,
            'anomalies_detected': 0,
            'anomaly_records_created': 0,
            'errors': [],
            'processing_time_seconds': 0
        }
        
        try:
            if not self.model.is_fitted:
                results['errors'].append("Model is not trained. Please train the model first.")
                return results
            
            # Get flight data
            flights = Flight.objects.filter(flight_id__in=flight_ids).order_by('flight_id', 'timestamp')
            
            if not flights.exists():
                results['errors'].append("No flights found for the provided flight IDs")
                return results
            
            # Convert to DataFrame
            flights_data = list(flights.values(
                'id', 'flight_id', 'aircraft_id', 'timestamp',
                'latitude', 'longitude', 'altitude', 'speed', 'heading'
            ))
            flights_df = pd.DataFrame(flights_data)
            
            # Predict anomalies
            is_anomaly, confidence_scores = self.model.predict_anomalies(flights_df)
            
            # Create anomaly detection records
            anomaly_records = []
            anomalies_count = 0
            
            for i, flight_record in enumerate(flights):
                if is_anomaly[i]:
                    confidence = float(confidence_scores[i])
                    
                    # Determine anomaly type based on features
                    anomaly_type = self._classify_anomaly_type(flights_df.iloc[i], confidence)
                    
                    # Create anomaly detection record
                    anomaly_detection = AnomalyDetection(
                        flight=flight_record,
                        anomaly_type=anomaly_type,
                        confidence_score=confidence,
                        ml_model_version=self.model.model_version,
                        anomaly_details={
                            'features': flights_df.iloc[i].to_dict(),
                            'confidence_score': confidence,
                            'model_contamination': self.model.contamination,
                            'detection_timestamp': timezone.now().isoformat()
                        }
                    )
                    anomaly_records.append(anomaly_detection)
                    anomalies_count += 1
            
            # Bulk create anomaly records
            if anomaly_records:
                AnomalyDetection.objects.bulk_create(anomaly_records, ignore_conflicts=True)
                self.logger.info(f"Created {len(anomaly_records)} anomaly detection records")
            
            results.update({
                'success': True,
                'processed_flights': len(flights),
                'anomalies_detected': anomalies_count,
                'anomaly_records_created': len(anomaly_records)
            })
            
            self.logger.info(f"Processed {len(flights)} flight records, detected {anomalies_count} anomalies")
            
        except Exception as e:
            error_msg = f"Error processing flight batch: {str(e)}"
            results['errors'].append(error_msg)
            self.logger.error(error_msg, exc_info=True)
        
        finally:
            results['processing_time_seconds'] = (timezone.now() - start_time).total_seconds()
        
        return results
    
    def _classify_anomaly_type(self, flight_data: pd.Series, confidence: float) -> str:
        """
        Classify the type of anomaly based on flight data
        
        Args:
            flight_data: Single flight record data
            confidence: Anomaly confidence score
            
        Returns:
            Anomaly type string
        """
        # Simple heuristic classification - can be enhanced with more sophisticated logic
        
        if abs(flight_data.get('altitude_change', 0)) > 5000:
            return 'altitude_anomaly'
        elif abs(flight_data.get('speed_change', 0)) > 100:
            return 'speed_anomaly'
        elif flight_data.get('distance_from_previous', 0) > 50:  # Large jump in position
            return 'route_deviation'
        elif confidence > 0.9:
            return 'combined'
        else:
            return 'temporal_anomaly'
    
    def run_full_pipeline(self, retrain: bool = False) -> Dict[str, Any]:
        """
        Run the complete anomaly detection pipeline
        
        Args:
            retrain: Whether to retrain the model
            
        Returns:
            Pipeline execution results
        """
        pipeline_start = timezone.now()
        results = {
            'success': False,
            'pipeline_steps': [],
            'total_processing_time_seconds': 0
        }
        
        try:
            # Step 1: Train or load model
            if retrain or not self.model.is_fitted:
                self.logger.info("Training anomaly detection model...")
                training_results = self.model.train()
                results['pipeline_steps'].append({
                    'step': 'model_training',
                    'results': training_results
                })
                
                if not training_results['success']:
                    results['error'] = "Model training failed"
                    return results
            
            # Step 2: Get all unique flight IDs
            flight_ids = list(Flight.objects.values_list('flight_id', flat=True).distinct())
            
            if not flight_ids:
                results['error'] = "No flights available for processing"
                return results
            
            # Step 3: Process flights in batches
            batch_size = 100  # Process 100 flights at a time
            total_processed = 0
            total_anomalies = 0
            
            for i in range(0, len(flight_ids), batch_size):
                batch_flight_ids = flight_ids[i:i + batch_size]
                batch_results = self.process_flight_batch(batch_flight_ids)
                
                total_processed += batch_results['processed_flights']
                total_anomalies += batch_results['anomalies_detected']
                
                if batch_results['errors']:
                    self.logger.warning(f"Batch processing errors: {batch_results['errors']}")
            
            results.update({
                'success': True,
                'total_flights_processed': total_processed,
                'total_anomalies_detected': total_anomalies,
                'pipeline_steps': results['pipeline_steps'] + [{
                    'step': 'anomaly_detection',
                    'flights_processed': total_processed,
                    'anomalies_detected': total_anomalies
                }]
            })
            
            self.logger.info(f"Pipeline completed: {total_processed} flights processed, {total_anomalies} anomalies detected")
            
        except Exception as e:
            error_msg = f"Pipeline execution failed: {str(e)}"
            results['error'] = error_msg
            self.logger.error(error_msg, exc_info=True)
        
        finally:
            results['total_processing_time_seconds'] = (timezone.now() - pipeline_start).total_seconds()
        
        return results