"""
Utility functions for flight data ingestion and processing.
"""

import csv
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Flight, DataSource

logger = logging.getLogger(__name__)


class DataIngestionError(Exception):
    """Custom exception for data ingestion errors"""
    pass


class CSVDataParser:
    """Parser for CSV flight data with validation and normalization"""
    
    # Expected CSV headers and their mappings
    HEADER_MAPPINGS = {
        'flight_id': ['flight_id', 'flightid', 'id', 'flight'],
        'aircraft_id': ['aircraft_id', 'aircraftid', 'aircraft', 'tail_number', 'registration'],
        'timestamp': ['timestamp', 'time', 'datetime', 'date_time'],
        'latitude': ['latitude', 'lat', 'y'],
        'longitude': ['longitude', 'lon', 'lng', 'x'],
        'altitude': ['altitude', 'alt', 'height'],
        'speed': ['speed', 'velocity', 'ground_speed', 'gs'],
        'heading': ['heading', 'track', 'course', 'direction'],
        'origin': ['origin', 'departure', 'from', 'orig'],
        'destination': ['destination', 'arrival', 'to', 'dest'],
    }
    
    def __init__(self, file_content: str, filename: str = None):
        """
        Initialize parser with CSV content
        
        Args:
            file_content: Raw CSV content as string
            filename: Optional filename for error reporting
        """
        self.file_content = file_content
        self.filename = filename or "unknown.csv"
        self.errors = []
        self.warnings = []
        self.parsed_data = []
        
    def parse(self) -> Tuple[List[Dict], List[str], List[str]]:
        """
        Parse CSV content and return validated data
        
        Returns:
            Tuple of (parsed_data, errors, warnings)
        """
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(self.file_content))
            
            # Validate headers
            headers = self._validate_and_map_headers(csv_reader.fieldnames)
            if not headers:
                return [], self.errors, self.warnings
            
            # Process each row
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                try:
                    parsed_row = self._parse_row(row, headers, row_num)
                    if parsed_row:
                        self.parsed_data.append(parsed_row)
                except Exception as e:
                    error_msg = f"Row {row_num}: {str(e)}"
                    self.errors.append(error_msg)
                    logger.warning(f"CSV parsing error in {self.filename}: {error_msg}")
            
            logger.info(f"CSV parsing completed for {self.filename}: "
                       f"{len(self.parsed_data)} valid rows, "
                       f"{len(self.errors)} errors, "
                       f"{len(self.warnings)} warnings")
            
        except Exception as e:
            error_msg = f"Failed to parse CSV file {self.filename}: {str(e)}"
            self.errors.append(error_msg)
            logger.error(error_msg)
        
        return self.parsed_data, self.errors, self.warnings
    
    def _validate_and_map_headers(self, fieldnames: List[str]) -> Optional[Dict[str, str]]:
        """
        Validate CSV headers and create mapping to model fields
        
        Args:
            fieldnames: List of CSV column headers
            
        Returns:
            Dictionary mapping CSV headers to model fields, or None if validation fails
        """
        if not fieldnames:
            self.errors.append("CSV file has no headers")
            return None
        
        # Normalize headers (lowercase, strip whitespace)
        normalized_headers = [header.lower().strip() for header in fieldnames]
        
        # Create mapping from CSV headers to model fields
        header_mapping = {}
        required_fields = ['latitude', 'longitude']  # Minimum required fields
        found_fields = set()
        
        for model_field, possible_headers in self.HEADER_MAPPINGS.items():
            for csv_header in normalized_headers:
                if csv_header in possible_headers:
                    header_mapping[fieldnames[normalized_headers.index(csv_header)]] = model_field
                    found_fields.add(model_field)
                    break
        
        # Check for required fields
        missing_required = set(required_fields) - found_fields
        if missing_required:
            self.errors.append(f"Missing required fields: {', '.join(missing_required)}")
            return None
        
        # Warn about missing optional fields
        optional_fields = ['flight_id', 'aircraft_id', 'timestamp', 'altitude', 'speed', 'heading']
        missing_optional = set(optional_fields) - found_fields
        if missing_optional:
            self.warnings.append(f"Missing optional fields: {', '.join(missing_optional)}")
        
        return header_mapping
    
    def _parse_row(self, row: Dict[str, str], header_mapping: Dict[str, str], row_num: int) -> Optional[Dict]:
        """
        Parse and validate a single CSV row
        
        Args:
            row: Raw CSV row data
            header_mapping: Mapping from CSV headers to model fields
            row_num: Row number for error reporting
            
        Returns:
            Parsed and validated row data, or None if validation fails
        """
        parsed_row = {}
        
        # Extract and validate each field
        for csv_header, model_field in header_mapping.items():
            raw_value = row.get(csv_header, '').strip()
            
            try:
                if model_field == 'latitude':
                    parsed_row['latitude'] = self._validate_latitude(raw_value)
                elif model_field == 'longitude':
                    parsed_row['longitude'] = self._validate_longitude(raw_value)
                elif model_field == 'altitude':
                    parsed_row['altitude'] = self._validate_altitude(raw_value)
                elif model_field == 'speed':
                    parsed_row['speed'] = self._validate_speed(raw_value)
                elif model_field == 'heading':
                    parsed_row['heading'] = self._validate_heading(raw_value)
                elif model_field == 'timestamp':
                    parsed_row['timestamp'] = self._validate_timestamp(raw_value)
                elif model_field in ['flight_id', 'aircraft_id', 'origin', 'destination']:
                    if raw_value:  # Only add if not empty
                        parsed_row[model_field] = self._validate_string_field(raw_value, model_field)
                        
            except ValueError as e:
                raise ValueError(f"Invalid {model_field}: {str(e)}")
        
        # Generate default values for missing required fields
        if 'flight_id' not in parsed_row:
            parsed_row['flight_id'] = f"FLIGHT_{row_num}_{int(timezone.now().timestamp())}"
        
        if 'aircraft_id' not in parsed_row:
            parsed_row['aircraft_id'] = f"AIRCRAFT_{row_num}"
        
        if 'timestamp' not in parsed_row:
            parsed_row['timestamp'] = timezone.now()
        
        # Set default values for optional numeric fields
        parsed_row.setdefault('altitude', 0)
        parsed_row.setdefault('speed', 0.0)
        parsed_row.setdefault('heading', 0.0)
        
        return parsed_row
    
    def _validate_latitude(self, value: str) -> float:
        """Validate latitude coordinate"""
        if not value:
            raise ValueError("Latitude is required")
        try:
            lat = float(value)
            if not -90.0 <= lat <= 90.0:
                raise ValueError(f"Latitude {lat} must be between -90 and 90 degrees")
            return lat
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(f"'{value}' is not a valid number")
            raise
    
    def _validate_longitude(self, value: str) -> float:
        """Validate longitude coordinate"""
        if not value:
            raise ValueError("Longitude is required")
        try:
            lng = float(value)
            if not -180.0 <= lng <= 180.0:
                raise ValueError(f"Longitude {lng} must be between -180 and 180 degrees")
            return lng
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(f"'{value}' is not a valid number")
            raise
    
    def _validate_altitude(self, value: str) -> int:
        """Validate altitude value"""
        if not value:
            return 0
        try:
            alt = int(float(value))  # Allow float input but convert to int
            if alt < -1000:
                raise ValueError(f"Altitude {alt} cannot be below -1000 feet")
            if alt > 60000:
                raise ValueError(f"Altitude {alt} cannot exceed 60,000 feet")
            return alt
        except ValueError as e:
            if "could not convert" in str(e) or "invalid literal" in str(e):
                raise ValueError(f"'{value}' is not a valid altitude")
            raise
    
    def _validate_speed(self, value: str) -> float:
        """Validate speed value"""
        if not value:
            return 0.0
        try:
            speed = float(value)
            if speed < 0:
                raise ValueError(f"Speed {speed} cannot be negative")
            if speed > 1000:
                raise ValueError(f"Speed {speed} cannot exceed 1000 knots")
            return speed
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(f"'{value}' is not a valid speed")
            raise
    
    def _validate_heading(self, value: str) -> float:
        """Validate heading value"""
        if not value:
            return 0.0
        try:
            heading = float(value)
            if not 0.0 <= heading <= 360.0:
                raise ValueError(f"Heading {heading} must be between 0 and 360 degrees")
            return heading
        except ValueError as e:
            if "could not convert" in str(e):
                raise ValueError(f"'{value}' is not a valid heading")
            raise
    
    def _validate_timestamp(self, value: str) -> datetime:
        """Validate and parse timestamp"""
        if not value:
            return timezone.now()
        
        # Try multiple timestamp formats
        timestamp_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%S.%f',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%Y-%m-%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y',
        ]
        
        for fmt in timestamp_formats:
            try:
                dt = datetime.strptime(value, fmt)
                # Make timezone aware
                if timezone.is_naive(dt):
                    dt = timezone.make_aware(dt)
                
                # Check if timestamp is reasonable (not too far in future)
                if dt > timezone.now() + timezone.timedelta(days=1):
                    raise ValueError(f"Timestamp {value} is too far in the future")
                
                return dt
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse timestamp '{value}'. Supported formats include: YYYY-MM-DD HH:MM:SS, ISO format, etc.")
    
    def _validate_string_field(self, value: str, field_name: str) -> str:
        """Validate string fields like flight_id, aircraft_id, etc."""
        if not value or not value.strip():
            raise ValueError(f"{field_name} cannot be empty")
        
        value = value.strip().upper()
        
        if field_name in ['flight_id']:
            if len(value) > 50:
                raise ValueError(f"{field_name} cannot exceed 50 characters")
        elif field_name in ['aircraft_id']:
            if len(value) > 20:
                raise ValueError(f"{field_name} cannot exceed 20 characters")
        elif field_name in ['origin', 'destination']:
            if len(value) < 3 or len(value) > 4:
                raise ValueError(f"Airport code must be 3-4 characters")
            if not value.isalpha():
                raise ValueError(f"Airport code must contain only letters")
        
        return value


class FlightDataIngestion:
    """Main class for handling flight data ingestion from various sources"""
    
    def __init__(self, data_source: DataSource = None):
        """
        Initialize data ingestion handler
        
        Args:
            data_source: Optional DataSource instance for tracking ingestion
        """
        self.data_source = data_source
        self.logger = logging.getLogger(__name__)
    
    def ingest_csv_data(self, file_content: str, filename: str = None) -> Dict[str, Any]:
        """
        Ingest flight data from CSV content
        
        Args:
            file_content: Raw CSV content as string
            filename: Optional filename for logging
            
        Returns:
            Dictionary with ingestion results
        """
        start_time = timezone.now()
        result = {
            'success': False,
            'processed_count': 0,
            'error_count': 0,
            'warning_count': 0,
            'errors': [],
            'warnings': [],
            'created_flights': [],
            'processing_time_seconds': 0
        }
        
        try:
            self.logger.info(f"Starting CSV data ingestion for file: {filename}")
            
            # Parse CSV data
            parser = CSVDataParser(file_content, filename)
            parsed_data, errors, warnings = parser.parse()
            
            result['errors'].extend(errors)
            result['warnings'].extend(warnings)
            result['error_count'] = len(errors)
            result['warning_count'] = len(warnings)
            
            if errors:
                self.logger.error(f"CSV parsing failed with {len(errors)} errors")
                return result
            
            # Process parsed data and create Flight objects
            created_flights = []
            processing_errors = []
            
            for row_data in parsed_data:
                try:
                    # Check if flight already exists
                    existing_flight = Flight.objects.filter(
                        flight_id=row_data['flight_id'],
                        timestamp=row_data['timestamp']
                    ).first()
                    
                    if existing_flight:
                        self.logger.debug(f"Skipping duplicate flight: {row_data['flight_id']}")
                        continue
                    
                    # Create new flight
                    flight = Flight.objects.create(**row_data)
                    created_flights.append(flight)
                    
                except Exception as e:
                    error_msg = f"Failed to create flight {row_data.get('flight_id', 'unknown')}: {str(e)}"
                    processing_errors.append(error_msg)
                    self.logger.error(error_msg)
            
            result['processed_count'] = len(created_flights)
            result['created_flights'] = [f.flight_id for f in created_flights]
            result['errors'].extend(processing_errors)
            result['error_count'] += len(processing_errors)
            
            # Update data source if provided
            if self.data_source:
                self.data_source.last_ingestion = timezone.now()
                self.data_source.save()
            
            result['success'] = len(created_flights) > 0
            
            self.logger.info(f"CSV ingestion completed: {len(created_flights)} flights created, "
                           f"{len(processing_errors)} processing errors")
            
        except Exception as e:
            error_msg = f"Unexpected error during CSV ingestion: {str(e)}"
            result['errors'].append(error_msg)
            result['error_count'] += 1
            self.logger.error(error_msg, exc_info=True)
        
        finally:
            result['processing_time_seconds'] = (timezone.now() - start_time).total_seconds()
        
        return result
    
    def validate_file_format(self, file_content: str, filename: str = None) -> Dict[str, Any]:
        """
        Validate file format without processing data
        
        Args:
            file_content: Raw file content
            filename: Optional filename
            
        Returns:
            Validation result dictionary
        """
        result = {
            'valid': False,
            'file_type': None,
            'errors': [],
            'warnings': [],
            'estimated_rows': 0,
            'detected_headers': []
        }
        
        try:
            # Check if it's CSV format
            if filename and filename.lower().endswith('.csv'):
                result['file_type'] = 'csv'
                
                # Quick validation
                csv_reader = csv.DictReader(io.StringIO(file_content))
                headers = csv_reader.fieldnames
                
                if headers:
                    result['detected_headers'] = headers
                    result['estimated_rows'] = len(file_content.split('\n')) - 1  # Rough estimate
                    
                    # Check for required fields
                    normalized_headers = [h.lower().strip() for h in headers]
                    has_lat = any(h in ['latitude', 'lat', 'y'] for h in normalized_headers)
                    has_lng = any(h in ['longitude', 'lon', 'lng', 'x'] for h in normalized_headers)
                    
                    if has_lat and has_lng:
                        result['valid'] = True
                    else:
                        result['errors'].append("Missing required coordinate fields (latitude/longitude)")
                else:
                    result['errors'].append("No headers detected in CSV file")
            else:
                result['errors'].append("Unsupported file format. Only CSV files are supported.")
        
        except Exception as e:
            result['errors'].append(f"File validation error: {str(e)}")
        
        return result


def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework
    Provides consistent error response format across the API
    """
    from rest_framework.views import exception_handler
    from rest_framework import status
    from rest_framework.response import Response
    from django.http import Http404
    from django.core.exceptions import ValidationError as DjangoValidationError
    from django.conf import settings
    import logging

    logger = logging.getLogger(__name__)

    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Log the error
        logger.error(f"API Error: {exc.__class__.__name__}: {str(exc)}", exc_info=True)
        
        # Customize the response format
        custom_response_data = {
            'error': True,
            'error_type': exc.__class__.__name__,
            'message': 'An error occurred while processing your request.',
            'details': None,
            'timestamp': timezone.now().isoformat(),
            'path': context.get('request').path if context.get('request') else None
        }

        # Handle specific exception types
        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                custom_response_data['details'] = exc.detail
                # Extract the first error message for the main message
                first_field = next(iter(exc.detail.keys()))
                first_error = exc.detail[first_field]
                if isinstance(first_error, list) and first_error:
                    custom_response_data['message'] = str(first_error[0])
                else:
                    custom_response_data['message'] = str(first_error)
            elif isinstance(exc.detail, list):
                custom_response_data['details'] = exc.detail
                custom_response_data['message'] = str(exc.detail[0]) if exc.detail else custom_response_data['message']
            else:
                custom_response_data['message'] = str(exc.detail)

        # Handle different status codes
        if response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['message'] = 'The requested resource was not found.'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['message'] = 'You do not have permission to perform this action.'
        elif response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['message'] = 'Authentication credentials were not provided or are invalid.'
        elif response.status_code == status.HTTP_400_BAD_REQUEST:
            custom_response_data['message'] = custom_response_data.get('message', 'Invalid request data.')
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            custom_response_data['message'] = 'Rate limit exceeded. Please try again later.'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'An internal server error occurred. Please try again later.'

        response.data = custom_response_data

    else:
        # Handle exceptions not caught by DRF
        if isinstance(exc, Http404):
            logger.warning(f"404 Not Found: {str(exc)}")
            response = Response({
                'error': True,
                'error_type': 'NotFound',
                'message': 'The requested resource was not found.',
                'details': str(exc),
                'timestamp': timezone.now().isoformat(),
                'path': context.get('request').path if context.get('request') else None
            }, status=status.HTTP_404_NOT_FOUND)
        
        elif isinstance(exc, DjangoValidationError):
            logger.warning(f"Validation Error: {str(exc)}")
            response = Response({
                'error': True,
                'error_type': 'ValidationError',
                'message': 'Validation failed.',
                'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
                'timestamp': timezone.now().isoformat(),
                'path': context.get('request').path if context.get('request') else None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            # Log unexpected errors
            logger.error(f"Unexpected error: {exc.__class__.__name__}: {str(exc)}", exc_info=True)
            response = Response({
                'error': True,
                'error_type': 'InternalServerError',
                'message': 'An unexpected error occurred. Please try again later.',
                'details': str(exc) if settings.DEBUG else None,
                'timestamp': timezone.now().isoformat(),
                'path': context.get('request').path if context.get('request') else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return response