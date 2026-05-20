"""
Google Earth Engine Integration for Satellite NDVI Analysis
Provides real-time vegetation health monitoring from space
"""
import ee
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import numpy as np

# Initialize Earth Engine
try:
    ee.Initialize()
    print("✅ Google Earth Engine initialized successfully")
except Exception as e:
    print(f"⚠️ GEE initialization: {e}")
    print("Run: earthengine authenticate --force")

class GEESatelliteService:
    """Fetch and process satellite imagery from Google Earth Engine"""
    
    def __init__(self):
        self.sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        self.landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        self.mods = ee.ImageCollection('MODIS/006/MOD13Q1')
    
    def get_ndvi_for_location(self, lat: float, lon: float, date: str = None) -> Dict:
        """
        Get NDVI for a single point location
        Useful for quick checks of specific fields
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        point = ee.Geometry.Point([lon, lat])
        
        # Get Sentinel-2 image
        image = (self.sentinel2
            .filterDate(f'{date}-01-01', date)
            .filterBounds(point)
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
            .first())
        
        # Calculate NDVI
        ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
        
        # Extract value at point
        value = ndvi.reduceRegion(
            reducer=ee.Reducer.first(),
            geometry=point,
            scale=10
        )
        
        try:
            ndvi_value = value.get('NDVI').getInfo()
            return {
                'location': {'lat': lat, 'lon': lon},
                'date': date,
                'ndvi': float(ndvi_value) if ndvi_value else None,
                'source': 'Sentinel-2 (10m resolution)',
                'interpretation': self.interpret_ndvi(float(ndvi_value)) if ndvi_value else 'No data'
            }
        except:
            return {'error': 'No recent cloud-free imagery available for this location'}
    
    def get_ndvi_for_boundary(self, coordinates: List[List[float]], start_date: str, end_date: str) -> Dict:
        """
        Get NDVI for a field boundary polygon
        coordinates: list of [lon, lat] points forming a polygon
        """
        try:
            # Create polygon from coordinates
            field_polygon = ee.Geometry.Polygon(coordinates)
            
            # Filter Sentinel-2 collection
            collection = (self.sentinel2
                .filterDate(start_date, end_date)
                .filterBounds(field_polygon)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)))
            
            # Calculate NDVI for all images
            def add_ndvi(image):
                ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
                return image.addBands(ndvi)
            
            with_ndvi = collection.map(add_ndvi)
            
            # Get median composite to reduce cloud effects
            median_ndvi = with_ndvi.select('NDVI').median()
            
            # Calculate statistics for the field
            stats = median_ndvi.reduceRegion(
                reducer=ee.Reducer.mean().combine(
                    ee.Reducer.stdDev(), None, True).combine(
                    ee.Reducer.minMax(), None, True),
                geometry=field_polygon,
                scale=10,
                bestEffort=True
            )
            
            # Get results
            stats_dict = stats.getInfo()
            
            mean_ndvi = stats_dict.get('NDVI_mean', 0)
            std_ndvi = stats_dict.get('NDVI_stdDev', 0)
            min_ndvi = stats_dict.get('NDVI_min', 0)
            max_ndvi = stats_dict.get('NDVI_max', 0)
            
            # Classify vegetation health
            healthy_pct = self.calculate_health_percentage(median_ndvi, field_polygon)
            
            return {
                'success': True,
                'mean_ndvi': round(mean_ndvi, 3),
                'min_ndvi': round(min_ndvi, 3),
                'max_ndvi': round(max_ndvi, 3),
                'std_ndvi': round(std_ndvi, 3),
                'healthy_percentage': healthy_pct,
                'interpretation': self.interpret_ndvi(mean_ndvi),
                'source': 'Sentinel-2 Satellite (10m resolution)',
                'period': f'{start_date} to {end_date}',
                'recommendation': self.generate_recommendation(mean_ndvi, healthy_pct)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_health_percentage(self, ndvi_image, polygon) -> float:
        """Calculate percentage of field that is healthy (NDVI > 0.4)"""
        healthy_mask = ndvi_image.gt(0.4)
        healthy_area = healthy_mask.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=polygon,
            scale=10,
            bestEffort=True
        )
        try:
            return round(healthy_area.getInfo().get('NDVI', 0) * 100, 1)
        except:
            return 0
    
    def get_historical_trend(self, coordinates: List[List[float]], months: int = 6) -> List[Dict]:
        """
        Get historical NDVI trend for a field
        Returns monthly NDVI values for trend analysis
        """
        field_polygon = ee.Geometry.Polygon(coordinates)
        trend_data = []
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=months*30)
        
        # Get monthly composites
        current = start_date
        while current <= end_date:
            month_start = current.strftime('%Y-%m-%d')
            month_end = (current + timedelta(days=30)).strftime('%Y-%m-%d')
            
            collection = (self.sentinel2
                .filterDate(month_start, month_end)
                .filterBounds(field_polygon)
                .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)))
            
            if collection.size().getInfo() > 0:
                def add_ndvi(img):
                    ndvi = img.normalizedDifference(['B8', 'B4']).rename('NDVI')
                    return img.addBands(ndvi)
                
                with_ndvi = collection.map(add_ndvi)
                median_ndvi = with_ndvi.select('NDVI').median()
                
                mean_ndvi = median_ndvi.reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=field_polygon,
                    scale=10,
                    bestEffort=True
                )
                
                try:
                    ndvi_value = mean_ndvi.getInfo().get('NDVI', None)
                    if ndvi_value:
                        trend_data.append({
                            'date': month_start,
                            'ndvi': round(ndvi_value, 3),
                            'label': current.strftime('%b %Y')
                        })
                except:
                    pass
            
            current += timedelta(days=30)
        
        # Calculate trend direction
        if len(trend_data) >= 2:
            first = trend_data[0]['ndvi']
            last = trend_data[-1]['ndvi']
            trend = 'improving' if last > first else 'declining' if last < first else 'stable'
            change = abs(last - first)
        else:
            trend = 'insufficient_data'
            change = 0
        
        return {
            'history': trend_data,
            'trend': trend,
            'change_percentage': round(change * 100, 1),
            'data_points': len(trend_data)
        }
    
    def interpret_ndvi(self, ndvi: float) -> str:
        """Interpret NDVI value for agricultural use"""
        if ndvi > 0.6:
            return "Excellent 🌟 - Very healthy vegetation"
        elif ndvi > 0.4:
            return "Good ✅ - Healthy vegetation"
        elif ndvi > 0.2:
            return "Moderate ⚠️ - Stressed vegetation"
        elif ndvi > 0:
            return "Poor 🚨 - Sparse vegetation"
        else:
            return "Barren ❌ - No vegetation / Water / Soil"
    
    def generate_recommendation(self, ndvi: float, healthy_pct: float) -> str:
        """Generate actionable farming recommendations"""
        if ndvi > 0.6 and healthy_pct > 70:
            return "✅ Excellent crop health. Maintain current practices. Consider harvest planning."
        elif ndvi > 0.4:
            return "⚠️ Moderate health. Apply targeted irrigation to areas with visible stress."
        elif ndvi > 0.2:
            return "🚨 Poor health detected. Apply nitrogen fertilizer and check for pest infestation."
        else:
            return "❌ Critical condition. Immediate intervention required. Consider replanting or soil amendment."
    
    def get_available_imagery(self, coordinates: List[List[float]]) -> Dict:
        """Check what satellite imagery is available for this location"""
        field_polygon = ee.Geometry.Polygon(coordinates)
        
        sentinel_count = self.sentinel2.filterBounds(field_polygon).size().getInfo()
        landsat_count = self.landsat.filterBounds(field_polygon).size().getInfo()
        
        return {
            'sentinel_2_images': sentinel_count,
            'landsat_8_images': landsat_count,
            'has_data': sentinel_count > 0 or landsat_count > 0
        }
