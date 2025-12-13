"""
Konfigurationsdatei für die Flask-Anwendung
"""
import os

class Config:
    """Base-Konfiguration"""
    # Flask
    DEBUG = True
    TESTING = False
    
    # TheMealDB API
    THEMEALDB_BASE_URL = "https://www.themealdb.com/api/json/v1/1"
    
    # Caching
    CACHE_TIMEOUT = 3600  # 1 Stunde


class DevelopmentConfig(Config):
    """Entwicklungs-Konfiguration"""
    DEBUG = True


class ProductionConfig(Config):
    """Produktions-Konfiguration"""
    DEBUG = False


class TestingConfig(Config):
    """Test-Konfiguration"""
    TESTING = True


# Config basierend auf Umgebungsvariable auswählen
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
