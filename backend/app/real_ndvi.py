"""
Real NDVI Calculator for Agricultural Monitoring
NDVI = (NIR - Red) / (NIR + Red)
"""
import numpy as np
import rasterio
from pathlib import Path

def calculate_real_ndvi(image_path):
    """
    Calculate actual NDVI from GeoTIFF image
    Requires multi-spectral imagery with Red and NIR bands
    """
    try:
        with rasterio.open(image_path) as src:
            # For Sentinel-2: Band 4 (Red), Band 8 (NIR)
            # For drone: Check your band order
            red_band = src.read(3)  # Red band
            nir_band = src.read(4)  # Near-Infrared band
            
            # Convert to float
            red = red_band.astype(np.float32)
            nir = nir_band.astype(np.float32)
            
            # Calculate NDVI
            ndvi = (nir - red) / (nir + red + 1e-10)
            
            # Statistics
            result = {
                'mean_ndvi': float(np.mean(ndvi)),
                'min_ndvi': float(np.min(ndvi)),
                'max_ndvi': float(np.max(ndvi)),
                'std_ndvi': float(np.std(ndvi)),
                'healthy_percentage': float(np.sum(ndvi > 0.4) / ndvi.size * 100),
                'moderate_percentage': float(np.sum((ndvi >= 0.2) & (ndvi <= 0.4)) / ndvi.size * 100),
                'poor_percentage': float(np.sum(ndvi < 0.2) / ndvi.size * 100)
            }
            
            return result
            
    except Exception as e:
        return {'error': str(e), 'note': 'Requires GeoTIFF with Red and NIR bands'}

def calculate_ndvi_from_rgb(image_path):
    """
    For RGB images (normal photos), use Green-Red Vegetation Index (GRVI)
    as a proxy for NDVI
    """
    from PIL import Image
    
    img = Image.open(image_path)
    img_array = np.array(img)
    
    if len(img_array.shape) == 3:
        r, g, b = img_array[:,:,0], img_array[:,:,1], img_array[:,:,2]
        
        # GRVI = (Green - Red) / (Green + Red)
        grvi = (g - r) / (g + r + 1e-10)
        grvi = np.clip(grvi, -0.5, 0.8)
        
        result = {
            'mean_ndvi': float(np.mean(grvi)),
            'healthy_percentage': float(np.sum(grvi > 0.2) / grvi.size * 100),
            'note': 'Calculated from RGB image using GRVI. For accurate NDVI, use multispectral imagery.'
        }
        
        return result
    
    return {'error': 'Invalid image format'}
