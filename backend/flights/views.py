from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .utils import detect_anomalies
import pandas as pd
import os

@api_view(['GET'])
def flight_anomalies(request, flight_id):
    path = f"../data/{flight_id}.csv"
    if not os.path.exists(path):
        return Response({"error": "Flight data not found"}, status=404)
    
    df = pd.read_csv(path)
    df = detect_anomalies(df)
    return Response(df.to_dict(orient="records"))
