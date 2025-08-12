"""
Unit tests for flight data ingestion functionality.
"""

import io
import tempfile
from datetime import datetime
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import Flight, DataSource
from .utils import CSVDataParser, FlightDataIngestion, DataIngestionError


class CSVDataParserTestCase(TestCase):
    """Test cases for CSVDataParser class"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_csv_content = """flight_id,aircraft_id,timestamp,lat,lon,altitude,speed,heading
FL001,AC001,2024-01-01 10:00:00,52.0,21.0,10000,450,90
FL002,AC002,2024-01-01 11:00:00,52.1,21.1,10020,455,95"""
        
        self.minimal_csv_content = """lat,lon
52.0,21.0
52.1,21.1"""
        
        self.invalid_csv_content = """invalid,headers
data1,data2"""
        
        self.malformed_csv_content = """lat,lon,altitude
52.0,21.0,abc
invalid_lat,21.1,10000"""
    
    def test_parse_valid_csv(self):
        """Test parsing valid CSV data"""
        parser = CSVDataParser(self.valid_csv_content, "test.csv")
        parsed_data, errors, warnings = parser.parse()
        
        self.assertEqual(len(parsed_data), 2)
        self.assertEqual(len(errors), 0)
        self.assertTrue(len(warnings) >= 0)  # May have warnings about missing optional fields
        
        # Check first row
        first_row = parsed_data[0]
        self.assertEqual(first_row['flight_id'], 'FL001')
        self.assertEqual(first_row['aircraft_id'], 'AC001')
        self.assertEqual(first_row['latitude'], 52.0)
        self.assertEqual(first_row['longitude'], 21.0)
        self.assertEqual(first_row['altitude'], 10000)
        self.assertEqual(first_row['speed'], 450.0)
        self.assertEqual(first_row['heading'], 90.0)
    
    def test_parse_minimal_csv(self):
        """Test parsing CSV with only required fields"""
        parser = CSVDataParser(self.minimal_csv_content, "minimal.csv")
        parsed_data, errors, warnings = parser.parse()
        
        self.assertEqual(len(parsed_data), 2)
        self.assertEqual(len(errors), 0)
        self.assertTrue(len(warnings) > 0)  # Should warn about missing optional fields
        
        # Check that default values are assigned
        first_row = parsed_data[0]
        self.assertTrue(first_row['flight_id'].startswith('FLIGHT_'))
        self.assertTrue(first_row['aircraft_id'].startswith('AIRCRAFT_'))
        self.assertEqual(first_row['latitude'], 52.0)
        self.assertEqual(first_row['longitude'], 21.0)
        self.assertEqual(first_row['altitude'], 0)
        self.assertEqual(first_row['speed'], 0.0)
        self.assertEqual(first_row['heading'], 0.0)
    
    def test_parse_invalid_headers(self):
        """Test parsing CSV with invalid headers"""
        parser = CSVDataParser(self.invalid_csv_content, "invalid.csv")
        parsed_data, errors, warnings = parser.parse()
        
        self.assertEqual(len(parsed_data), 0)
        self.assertTrue(len(errors) > 0)
        self.assertIn("Missing required fields", errors[0])
    
    def test_parse_malformed_data(self):
        """Test parsing CSV with malformed data"""
        parser = CSVDataParser(self.malformed_csv_content, "malformed.csv")
        parsed_data, errors, warnings = parser.parse()
        
        self.assertTrue(len(errors) > 0)
        # Should have errors for invalid altitude and latitude
        error_text = ' '.join(errors)
        self.assertIn("altitude", error_text.lower())
    
    def test_validate_latitude(self):
        """Test latitude validation"""
        parser = CSVDataParser("", "test.csv")
        
        # Valid latitudes
        self.assertEqual(parser._validate_latitude("52.0"), 52.0)
        self.assertEqual(parser._validate_latitude("-90"), -90.0)
        self.assertEqual(parser._validate_latitude("90"), 90.0)
        
        # Invalid latitudes
        with self.assertRaises(ValueError):
            parser._validate_latitude("91")  # Too high
        with self.assertRaises(ValueError):
            parser._validate_latitude("-91")  # Too low
        with self.assertRaises(ValueError):
            parser._validate_latitude("abc")  # Not a number
        with self.assertRaises(ValueError):
            parser._validate_latitude("")  # Empty
    
    def test_validate_longitude(self):
        """Test longitude validation"""
        parser = CSVDataParser("", "test.csv")
        
        # Valid longitudes
        self.assertEqual(parser._validate_longitude("21.0"), 21.0)
        self.assertEqual(parser._validate_longitude("-180"), -180.0)
        self.assertEqual(parser._validate_longitude("180"), 180.0)
        
        # Invalid longitudes
        with self.assertRaises(ValueError):
            parser._validate_longitude("181")  # Too high
        with self.assertRaises(ValueError):
            parser._validate_longitude("-181")  # Too low
        with self.assertRaises(ValueError):
            parser._validate_longitude("xyz")  # Not a number
    
    def test_validate_altitude(self):
        """Test altitude validation"""
        parser = CSVDataParser("", "test.csv")
        
        # Valid altitudes
        self.assertEqual(parser._validate_altitude("10000"), 10000)
        self.assertEqual(parser._validate_altitude("0"), 0)
        self.assertEqual(parser._validate_altitude("-500"), -500)
        
        # Invalid altitudes
        with self.assertRaises(ValueError):
            parser._validate_altitude("-1001")  # Too low
        with self.assertRaises(ValueError):
            parser._validate_altitude("60001")  # Too high
        with self.assertRaises(ValueError):
            parser._validate_altitude("abc")  # Not a number
    
    def test_validate_speed(self):
        """Test speed validation"""
        parser = CSVDataParser("", "test.csv")
        
        # Valid speeds
        self.assertEqual(parser._validate_speed("450"), 450.0)
        self.assertEqual(parser._validate_speed("0"), 0.0)
        self.assertEqual(parser._validate_speed("999.5"), 999.5)
        
        # Invalid speeds
        with self.assertRaises(ValueError):
            parser._validate_speed("-1")  # Negative
        with self.assertRaises(ValueError):
            parser._validate_speed("1001")  # Too high
        with self.assertRaises(ValueError):
            parser._validate_speed("fast")  # Not a number
    
    def test_validate_heading(self):
        """Test heading validation"""
        parser = CSVDataParser("", "test.csv")
        
        # Valid headings
        self.assertEqual(parser._validate_heading("90"), 90.0)
        self.assertEqual(parser._validate_heading("0"), 0.0)
        self.assertEqual(parser._validate_heading("360"), 360.0)
        
        # Invalid headings
        with self.assertRaises(ValueError):
            parser._validate_heading("-1")  # Too low
        with self.assertRaises(ValueError):
            parser._validate_heading("361")  # Too high
        with self.assertRaises(ValueError):
            parser._validate_heading("north")  # Not a number
    
    def test_validate_timestamp(self):
        """Test timestamp validation"""
        parser = CSVDataParser("", "test.csv")
        
        # Valid timestamps
        dt1 = parser._validate_timestamp("2024-01-01 10:00:00")
        self.assertIsInstance(dt1, datetime)
        
        dt2 = parser._validate_timestamp("2024-01-01T10:00:00Z")
        self.assertIsInstance(dt2, datetime)
        
        dt3 = parser._validate_timestamp("2024-01-01")
        self.assertIsInstance(dt3, datetime)
        
        # Empty timestamp should return current time
        dt4 = parser._validate_timestamp("")
        self.assertIsInstance(dt4, datetime)
        
        # Invalid timestamp
        with self.assertRaises(ValueError):
            parser._validate_timestamp("invalid-date")
    
    def test_validate_string_fields(self):
        """Test string field validation"""
        parser = CSVDataParser("", "test.csv")
        
        # Valid flight_id
        self.assertEqual(parser._validate_string_field("FL001", "flight_id"), "FL001")
        
        # Valid aircraft_id
        self.assertEqual(parser._validate_string_field("ac001", "aircraft_id"), "AC001")
        
        # Valid airport codes
        self.assertEqual(parser._validate_string_field("jfk", "origin"), "JFK")
        self.assertEqual(parser._validate_string_field("EGLL", "destination"), "EGLL")
        
        # Invalid cases
        with self.assertRaises(ValueError):
            parser._validate_string_field("", "flight_id")  # Empty
        with self.assertRaises(ValueError):
            parser._validate_string_field("AB", "origin")  # Too short
        with self.assertRaises(ValueError):
            parser._validate_string_field("ABCDE", "origin")  # Too long
        with self.assertRaises(ValueError):
            parser._validate_string_field("AB1", "origin")  # Contains numbers


class FlightDataIngestionTestCase(TestCase):
    """Test cases for FlightDataIngestion class"""
    
    def setUp(self):
        """Set up test data"""
        self.data_source = DataSource.objects.create(
            name="Test CSV Source",
            source_type="csv_upload",
            is_active=True
        )
        
        self.valid_csv_content = """flight_id,aircraft_id,timestamp,lat,lon,altitude,speed,heading
FL001,AC001,2024-01-01 10:00:00,52.0,21.0,10000,450,90
FL002,AC002,2024-01-01 11:00:00,52.1,21.1,10020,455,95"""
        
        self.duplicate_csv_content = """flight_id,aircraft_id,timestamp,lat,lon,altitude,speed,heading
FL001,AC001,2024-01-01 10:00:00,52.0,21.0,10000,450,90
FL001,AC001,2024-01-01 10:00:00,52.0,21.0,10000,450,90"""
    
    def test_ingest_valid_csv_data(self):
        """Test ingesting valid CSV data"""
        ingestion = FlightDataIngestion(self.data_source)
        result = ingestion.ingest_csv_data(self.valid_csv_content, "test.csv")
        
        self.assertTrue(result['success'])
        self.assertEqual(result['processed_count'], 2)
        self.assertEqual(result['error_count'], 0)
        self.assertEqual(len(result['created_flights']), 2)
        
        # Verify flights were created in database
        self.assertEqual(Flight.objects.count(), 2)
        flight1 = Flight.objects.get(flight_id='FL001')
        self.assertEqual(flight1.aircraft_id, 'AC001')
        self.assertEqual(flight1.latitude, 52.0)
        self.assertEqual(flight1.longitude, 21.0)
    
    def test_ingest_duplicate_data(self):
        """Test ingesting duplicate flight data"""
        ingestion = FlightDataIngestion(self.data_source)
        
        # First ingestion
        result1 = ingestion.ingest_csv_data(self.valid_csv_content, "test1.csv")
        self.assertTrue(result1['success'])
        self.assertEqual(result1['processed_count'], 2)
        
        # Second ingestion with same data
        result2 = ingestion.ingest_csv_data(self.duplicate_csv_content, "test2.csv")
        self.assertFalse(result2['success'])  # No new flights created
        self.assertEqual(result2['processed_count'], 0)
        
        # Should still have only 2 flights in database
        self.assertEqual(Flight.objects.count(), 2)
    
    def test_ingest_invalid_csv_data(self):
        """Test ingesting invalid CSV data"""
        invalid_csv = """invalid,headers
data1,data2"""
        
        ingestion = FlightDataIngestion(self.data_source)
        result = ingestion.ingest_csv_data(invalid_csv, "invalid.csv")
        
        self.assertFalse(result['success'])
        self.assertEqual(result['processed_count'], 0)
        self.assertTrue(result['error_count'] > 0)
        self.assertTrue(len(result['errors']) > 0)
    
    def test_validate_file_format_valid(self):
        """Test file format validation with valid CSV"""
        ingestion = FlightDataIngestion()
        result = ingestion.validate_file_format(self.valid_csv_content, "test.csv")
        
        self.assertTrue(result['valid'])
        self.assertEqual(result['file_type'], 'csv')
        self.assertTrue(len(result['detected_headers']) > 0)
        self.assertTrue(result['estimated_rows'] > 0)
    
    def test_validate_file_format_invalid(self):
        """Test file format validation with invalid CSV"""
        invalid_csv = """invalid,headers
data1,data2"""
        
        ingestion = FlightDataIngestion()
        result = ingestion.validate_file_format(invalid_csv, "invalid.csv")
        
        self.assertFalse(result['valid'])
        self.assertEqual(result['file_type'], 'csv')
        self.assertTrue(len(result['errors']) > 0)


class CSVUploadAPITestCase(APITestCase):
    """Test cases for CSV upload API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.valid_csv_content = b"""flight_id,aircraft_id,timestamp,lat,lon,altitude,speed,heading
FL001,AC001,2024-01-01 10:00:00,52.0,21.0,10000,450,90
FL002,AC002,2024-01-01 11:00:00,52.1,21.1,10020,455,95"""
        
        self.minimal_csv_content = b"""lat,lon
52.0,21.0
52.1,21.1"""
        
        self.invalid_csv_content = b"""invalid,headers
data1,data2"""
    
    def test_upload_valid_csv(self):
        """Test uploading valid CSV file"""
        csv_file = SimpleUploadedFile(
            "test_flights.csv",
            self.valid_csv_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/flights/upload_csv/', {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['processed_count'], 2)
        self.assertEqual(response.data['error_count'], 0)
        
        # Verify flights were created
        self.assertEqual(Flight.objects.count(), 2)
    
    def test_upload_minimal_csv(self):
        """Test uploading CSV with minimal required fields"""
        csv_file = SimpleUploadedFile(
            "minimal_flights.csv",
            self.minimal_csv_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/flights/upload_csv/', {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['processed_count'], 2)
        self.assertTrue(response.data['warning_count'] > 0)  # Should have warnings about missing fields
    
    def test_upload_invalid_csv(self):
        """Test uploading invalid CSV file"""
        csv_file = SimpleUploadedFile(
            "invalid_flights.csv",
            self.invalid_csv_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/flights/upload_csv/', {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['processed_count'], 0)
        self.assertTrue(response.data['error_count'] > 0)
    
    def test_upload_no_file(self):
        """Test upload endpoint without file"""
        response = self.client.post('/api/flights/upload_csv/', {}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No file provided', response.data['error'])
    
    def test_upload_wrong_file_type(self):
        """Test uploading non-CSV file"""
        txt_file = SimpleUploadedFile(
            "test.txt",
            b"This is not a CSV file",
            content_type="text/plain"
        )
        
        response = self.client.post('/api/flights/upload_csv/', {'file': txt_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid file type', response.data['error'])
    
    def test_upload_large_file(self):
        """Test uploading file that exceeds size limit"""
        # Create a large CSV content (over 50MB)
        large_content = b"lat,lon\n" + b"52.0,21.0\n" * 3000000  # Approximately 54MB
        
        large_file = SimpleUploadedFile(
            "large_file.csv",
            large_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/flights/upload_csv/', {'file': large_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('File too large', response.data['error'])
    
    def test_validate_csv_endpoint(self):
        """Test CSV validation endpoint"""
        csv_file = SimpleUploadedFile(
            "test_flights.csv",
            self.valid_csv_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/flights/validate_csv/', {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['valid'])
        self.assertEqual(response.data['file_type'], 'csv')
        self.assertTrue(len(response.data['detected_headers']) > 0)
        self.assertTrue(response.data['estimated_rows'] > 0)
    
    def test_validate_invalid_csv_endpoint(self):
        """Test CSV validation endpoint with invalid file"""
        csv_file = SimpleUploadedFile(
            "invalid.csv",
            self.invalid_csv_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/flights/validate_csv/', {'file': csv_file}, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['valid'])
        self.assertTrue(len(response.data['errors']) > 0)
    
    @patch('flights.utils.logger')
    def test_error_logging(self, mock_logger):
        """Test that errors are properly logged"""
        csv_file = SimpleUploadedFile(
            "invalid.csv",
            self.invalid_csv_content,
            content_type="text/csv"
        )
        
        response = self.client.post('/api/flights/upload_csv/', {'file': csv_file}, format='multipart')
        
        # Verify that error logging was called
        mock_logger.error.assert_called()
        mock_logger.info.assert_called()


class DataIngestionErrorHandlingTestCase(TestCase):
    """Test cases for error handling in data ingestion"""
    
    def test_malformed_csv_handling(self):
        """Test handling of malformed CSV data"""
        malformed_csv = """lat,lon,altitude
52.0,21.0,abc
invalid_lat,21.1,10000
,21.2,5000"""
        
        parser = CSVDataParser(malformed_csv, "malformed.csv")
        parsed_data, errors, warnings = parser.parse()
        
        # Should have errors for each malformed row
        self.assertTrue(len(errors) > 0)
        # Should have fewer parsed rows than input rows
        self.assertTrue(len(parsed_data) < 3)
    
    def test_encoding_error_handling(self):
        """Test handling of encoding errors"""
        # This would be tested in the view layer where file encoding is handled
        pass
    
    def test_database_error_handling(self):
        """Test handling of database errors during ingestion"""
        valid_csv = """lat,lon
52.0,21.0"""
        
        ingestion = FlightDataIngestion()
        
        # Mock a database error
        with patch('flights.models.Flight.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database connection error")
            
            result = ingestion.ingest_csv_data(valid_csv, "test.csv")
            
            self.assertFalse(result['success'])
            self.assertTrue(result['error_count'] > 0)
            self.assertIn("Database connection error", str(result['errors']))
    
    def test_memory_handling_large_files(self):
        """Test memory handling for large CSV files"""
        # Create a moderately large CSV content
        large_csv_lines = ["lat,lon"]
        for i in range(10000):
            lat_val = 52.0 + (i % 100) / 1000.0
            lon_val = 21.0 + (i % 100) / 1000.0
            large_csv_lines.append(f"{lat_val},{lon_val}")
        
        large_csv = "\n".join(large_csv_lines)
        
        parser = CSVDataParser(large_csv, "large.csv")
        parsed_data, errors, warnings = parser.parse()
        
        # Should handle large files without memory issues
        self.assertTrue(len(parsed_data) > 0)
        self.assertEqual(len(errors), 0)