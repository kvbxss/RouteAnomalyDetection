from django.contrib import admin
from .models import Flight, AnomalyDetection, DataSource


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    """Admin interface for Flight model"""
    list_display = ['flight_id', 'aircraft_id', 'timestamp', 'origin', 'destination', 'altitude', 'speed']
    list_filter = ['origin', 'destination', 'timestamp']
    search_fields = ['flight_id', 'aircraft_id', 'origin', 'destination']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-timestamp']
    
    fieldsets = (
        ('Flight Information', {
            'fields': ('flight_id', 'aircraft_id', 'origin', 'destination')
        }),
        ('Location & Time', {
            'fields': ('timestamp', 'latitude', 'longitude', 'altitude')
        }),
        ('Flight Data', {
            'fields': ('speed', 'heading', 'route_points')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    """Admin interface for AnomalyDetection model"""
    list_display = ['flight', 'anomaly_type', 'confidence_score', 'detected_at', 'is_reviewed', 'is_false_positive']
    list_filter = ['anomaly_type', 'is_reviewed', 'is_false_positive', 'detected_at', 'ml_model_version']
    search_fields = ['flight__flight_id', 'flight__aircraft_id']
    readonly_fields = ['detected_at']
    ordering = ['-detected_at']
    
    fieldsets = (
        ('Detection Information', {
            'fields': ('flight', 'anomaly_type', 'confidence_score', 'ml_model_version')
        }),
        ('Review Status', {
            'fields': ('is_reviewed', 'is_false_positive', 'reviewer_notes')
        }),
        ('Details', {
            'fields': ('anomaly_details', 'detected_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    """Admin interface for DataSource model"""
    list_display = ['name', 'source_type', 'is_active', 'last_ingestion', 'is_overdue']
    list_filter = ['source_type', 'is_active']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at', 'is_overdue']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'source_type', 'is_active')
        }),
        ('Configuration', {
            'fields': ('endpoint_url', 'api_key', 'ingestion_frequency_minutes')
        }),
        ('Status', {
            'fields': ('last_ingestion', 'is_overdue')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'
