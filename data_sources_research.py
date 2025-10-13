#!/usr/bin/env python3
"""
Phase 1: Automated Data Sources Research for North India Crop Prediction

Target States: Punjab, Haryana, Uttar Pradesh, Bihar, Madhya Pradesh
Major Crops: Rice, Wheat, Maize
Requirement: Fully automated, open source/free data sources only
"""

import requests
import json
import pandas as pd
from datetime import datetime, timedelta
import os
from pathlib import Path

class DataSourceResearcher:
    def __init__(self):
        self.data_sources = {}
        self.target_states = ['Punjab', 'Haryana', 'Uttar Pradesh', 'Bihar', 'Madhya Pradesh']
        self.crops = ['Rice', 'Wheat', 'Maize']
        os.makedirs('data/research', exist_ok=True)
        os.makedirs('data/raw', exist_ok=True)

    def research_world_bank_data(self):
        """Research World Bank Open Data API for crop yields"""
        print("🔍 Researching World Bank Agricultural Data...")

        try:
            # World Bank API for agricultural indicators
            base_url = "https://api.worldbank.org/v2/indicator"
            crop_indicators = {
                'AG.YLD.CREL.KG': 'Cereal yield (kg per hectare)',
                'AG.PRD.CREL.MT': 'Cereal production (metric tons)',
                'AG.LND.CREL.HA': 'Cereal harvested area (hectares)',
                'SP.POP.TOTL': 'Total population',
                'AG.LND.TOTL.K2': 'Land area (sq. km)'
            }

            wb_data = {}

            for indicator, name in crop_indicators.items():
                url = f"{base_url}/{indicator}?format=json&country=IND&per_page=100"
                response = requests.get(url, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    if len(data) > 1 and data[1]:
                        wb_data[indicator] = data[1]
                        print(f"✅ Found data for: {name}")
                    else:
                        print(f"❌ No data for: {name}")

            self.data_sources['world_bank'] = {
                'available': bool(wb_data),
                'indicators': wb_data,
                'api_url': base_url,
                'temporal_coverage': '1960-present',
                'geographical_level': 'Country level (IND)',
                'automated_access': True
            }

        except Exception as e:
            print(f"⚠️  World Bank API error: {e}")
            self.data_sources['world_bank'] = {'available': False, 'error': str(e)}

    def research_faostat_data(self):
        """Research FAO FAOSTAT API via HTTP endpoints"""
        print("\n🔍 Researching FAO FAOSTAT Open Data...")

        try:
            # FAOSTAT meta data API
            fao_meta_url = "https://fenixservices.fao.org/faostat/api/v1/en/metadata"
            response = requests.get(fao_meta_url, timeout=30)

            if response.status_code == 200:
                meta_data = response.json()
                crop_datasets = [d for d in meta_data['results'] if 'crop' in d['Title'].lower()]

                # Test crop yields dataset access
                crop_query_url = "https://fenixservices.fao.org/faostat/api/v1/en/data/RL?area=India&element=Yield"
                crop_response = requests.get(crop_query_url, timeout=30)

                faostat_available = crop_response.status_code == 200
                if faostat_available:
                    crop_data = crop_response.json()
                    sample_data = crop_data['data'][:5] if 'data' in crop_data else []
                else:
                    sample_data = []

                self.data_sources['faostat'] = {
                    'available': faostat_available,
                    'datasets': crop_datasets[:3],  # Top 3 crop-related
                    'sample_data': sample_data,
                    'api_url': 'https://fenixservices.fao.org/faostat/api/v1/en/',
                    'temporal_coverage': '1961-present',
                    'geographical_level': 'Country/region level',
                    'automated_access': faostat_available,
                    'tested_endpoint': crop_query_url
                }

                print(f"✅ FAOSTAT API: {'Available' if faostat_available else 'Limited'}")

            else:
                print(f"❌ FAOSTAT API access failed: {response.status_code}")
                self.data_sources['faostat'] = {'available': False, 'error': response.status_code}

        except Exception as e:
            print(f"⚠️  FAOSTAT research error: {e}")
            self.data_sources['faostat'] = {'available': False, 'error': str(e)}

    def research_indian_government_data(self):
        """Research Indian government open data portals"""
        print("\n🔍 Researching Indian Government Open Data...")

        government_sources = [
            {
                'name': 'data.gov.in',
                'base_url': 'https://api.data.gov.in/resource',
                'test_endpoint': 'https://api.data.gov.in/resource/35b274de-d86e-4e6c-8e3a-b2f3b1e7f6b9?api-key=demo&format=json&offset=0&limit=5',
                'expected_data': 'crop_production'
            },
            {
                'name': 'Ministry of Agriculture API',
                'base_url': 'https://agmarknet.gov.in',
                'test_endpoint': 'https://agmarknet.gov.in/SearchCmmReport.aspx',  # Web scraping needed
                'expected_data': 'market_prices'
            },
            {
                'name': 'Indian Meteorological Department',
                'base_url': 'https://imdpune.gov.in',
                'test_endpoint': 'https://imdpune.gov.in/city_weather/forecast.php?city=Pune',
                'expected_data': 'weather_data'
            }
        ]

        govt_data_results = {}

        for source in government_sources:
            try:
                response = requests.get(source['test_endpoint'], timeout=30,
                                      headers={'User-Agent': 'Mozilla/5.0'})

                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    has_data = 'json' in content_type or 'text' in response.text[:100]

                    govt_data_results[source['name']] = {
                        'available': True,
                        'api_url': source['base_url'],
                        'response_status': response.status_code,
                        'data_format': content_type,
                        'has_sample_data': has_data
                    }

                    print(f"✅ {source['name']}: API accessible")

                else:
                    govt_data_results[source['name']] = {
                        'available': False,
                        'error': f'HTTP {response.status_code}'
                    }
                    print(f"❌ {source['name']}: {response.status_code}")

            except Exception as e:
                govt_data_results[source['name']] = {
                    'available': False,
                    'error': str(e)
                }
                print(f"⚠️  {source['name']}: {str(e)[:50]}...")

        self.data_sources['indian_govt'] = govt_data_results

    def research_climate_data_sources(self):
        """Research free climate/weather data sources"""
        print("\n🔍 Researching Climate/Weather Data Sources...")

        climate_sources = {
            'open_meteo': {
                'api_url': 'https://api.open-meteo.com/v1/forecast',
                'test_url': 'https://api.open-meteo.com/v1/forecast?latitude=30.9&longitude=75.85&hourly=temperature_2m&forecast_days=1',
                'temporal_coverage': 'Current + forecast',
                'automated': True,
                'rate_limit': '10,000/hour'
            },
            'nasa_power': {
                'api_url': 'https://power.larc.nasa.gov/api/temporal/daily/point',
                'test_url': 'https://power.larc.nasa.gov/api/temporal/daily/point?start=20200101&end=20200101&latitude=30.9&longitude=75.85&community=re&parameters=T2M&format=json',
                'temporal_coverage': '1981-present',
                'automated': True,
                'rate_limit': '1000/hour'
            },
            'cdsapi_era5': {
                'api_url': 'https://cds.climate.copernicus.eu/api/v2',
                'note': 'Requires free account, programmatic access',
                'temporal_coverage': '1950-present',
                'requirements': 'API key, small quota'
            }
        }

        climate_results = {}

        for name, config in climate_sources.items():
            if 'test_url' in config:
                try:
                    response = requests.get(config['test_url'], timeout=15)
                    success = response.status_code == 200

                    climate_results[name] = {
                        'available': success,
                        'api_url': config['api_url'],
                        'temporal_coverage': config.get('temporal_coverage', 'Unknown'),
                        'automated': config.get('automated', False),
                        'requirements': config.get('requirements', 'None'),
                        'rate_limit': config.get('rate_limit', 'Unknown'),
                        'test_response': response.status_code
                    }

                    print(f"✅ {name}: {'Available' if success else 'Failed'}")

                except Exception as e:
                    climate_results[name] = {
                        'available': False,
                        'error': str(e)[:100]
                    }
                    print(f"⚠️  {name}: {str(e)[:50]}...")

            else:
                climate_results[name] = config.copy()
                climate_results[name]['available'] = True  # Manual setup required
                print(f"ℹ️  {name}: Manual setup required")

        self.data_sources['climate_weather'] = climate_results

    def research_geospatial_data(self):
        """Research geospatial boundaries and agricultural data"""
        print("\n🔍 Researching Geospatial & Administrative Data...")

        geospatial_sources = {
            'gadm_boundaries': {
                'description': 'Global Administrative Areas database',
                'url': 'https://gadm.org/download_world.html',
                'file_url': 'https://biogeo.ucdavis.edu/data/gadm/gadm4.1/shp/gadm41_IND_shp.zip',
                'automated': True,
                'outdated': False
            },
            'natural_earth': {
                'description': 'Natural Earth administrative boundaries',
                'url': 'https://www.naturalearthdata.com',
                'api_access': False,
                'automated': False
            },
            'osm_boundaries': {
                'description': 'OpenStreetMap administrative boundaries',
                'library': 'osmnx',
                'automated': True,
                'python_api': True
            },
            'cropland_extent': {
                'description': 'Global cropland extent maps',
                'source': 'EarthStat (Geotiff downloads)',
                'url': 'https://www.earthstat.org/cropland-data/',
                'automated': False
            }
        }

        # Test GADM automated access
        gadm_config = geospatial_sources['gadm_boundaries']
        try:
            response = requests.head(gadm_config['file_url'], timeout=15)
            gadm_available = response.status_code == 200

            self.data_sources['geospatial'] = {
                'gadm': {
                    'available': gadm_available,
                    'url': gadm_config['file_url'],
                    'automated': True,
                    'size_estimate': '~50MB',
                    'contains_states': ['Punjab', 'Haryana', 'Uttar Pradesh', 'Bihar', 'Madhya Pradesh']
                },
                'osm_boundaries': {
                    'available': True,
                    'library': 'osmnx',
                    'automated': True,
                    'python_api': True,
                    'real_time': True
                }
            }

            print(f"✅ GADM boundaries: {'Available' if gadm_available else 'Failed'}")
            print("✅ OSM boundaries: Available via API")

        except Exception as e:
            print(f"⚠️  Geospatial data test failed: {e}")
            self.data_sources['geospatial'] = geospatial_sources

    def research_agricultural_zones(self):
        """Research agricultural zoning and land use data"""
        print("\n🔍 Researching Agricultural Zoning Data...")

        ag_sources = {
            'soilgrids': {
                'description': 'Global soil properties maps',
                'url': 'https://soilgrids.org',
                'api_url': 'https://rest.soilgrids.org/query',
                'test_url': 'https://rest.soilgrids.org/query?lon=75.85&lat=30.9',
                'properties': ['pH', 'organic_carbon', 'sand', 'clay']
            },
            'irrigation': {
                'description': 'Global irrigation maps',
                'source': 'GEM (Global Map of Irrigated Areas)',
                'url': 'https://www.iwmigem.org',
                'automated': True
            },
            'crop_distribution': {
                'description': 'SPAM crop distribution maps',
                'source': 'MapSPAM (Spatial Production Allocation Model)',
                'url': 'https://www.mapspam.info',
                'covers_india': True,
                'crops': ['Rice', 'Wheat', 'Maize']
            }
        }

        ag_results = {}

        # Test SoilGrids API
        soilgrids_config = ag_sources['soilgrids']
        try:
            response = requests.get(soilgrids_config['test_url'], timeout=15)
            soilgrids_available = response.status_code == 200

            ag_results['soilgrids'] = {
                'available': soilgrids_available,
                'api_url': soilgrids_config['url'],
                'properties': soilgrids_config['properties'],
                'global_coverage': True,
                'resolution': '250m',
                'automated': True
            }

            print(f"✅ SoilGrids API: {'Available' if soilgrids_available else 'Failed'}")

        except Exception as e:
            ag_results['soilgrids'] = {'available': False, 'error': str(e)[:100]}
            print(f"⚠️  SoilGrids test failed: {e}")

        ag_results.update(ag_sources)

        self.data_sources['agricultural_zones'] = ag_results

    def generate_data_requirements_summary(self):
        """Generate comprehensive requirements summary"""
        print("\n" + "="*60)
        print("📊 NORTH INDIA CROP PREDICTION - DATA REQUIREMENTS SUMMARY")
        print("="*60)

        total_sources = 0
        automated_sources = 0
        usable_sources = 0

        key_gaps = []
        priorities = []

        for category, sources in self.data_sources.items():
            print(f"\n🔸 {category.upper().replace('_', ' ')}:")

            # Handle both dict and direct bool values
            if isinstance(sources, dict):
                sources_iter = sources.items()
            else:
                sources_iter = [('main', sources)]

            for source_name, source_info in sources_iter:
                total_sources += 1

                # Handle different data structures
                if isinstance(source_info, dict):
                    available = source_info.get('available', False)
                else:
                    available = bool(source_info)

                if available:
                    usable_sources += 1
                    # Handle different data structures safely
                    if isinstance(source_info, dict):
                        automated = source_info.get('automated', source_info.get('automated_access', False))
                    else:
                        automated = True  # Assume automated if no structure

                    if automated:
                        automated_sources += 1
                        status = "✅ AUTOMATED"
                    else:
                        status = "⚠️  MANUAL"
                else:
                    status = "❌ UNAVAILABLE"
                    if isinstance(source_info, dict) and 'error' in source_info:
                        key_gaps.append(f"{source_name}: {source_info['error']}")
                    elif isinstance(source_info, (str, int)) and not available:
                        key_gaps.append(f"{source_name}: No data available")

                # Safe temporal and geo level access
                if isinstance(source_info, dict):
                    temporal = source_info.get('temporal_coverage', 'Unknown')
                    geo_level = source_info.get('geographical_level', 'Unknown')
                else:
                    temporal = geo_level = 'Unknown'

                print(f"   {status} {source_name}")
                if available:
                    print(f"      📅 {temporal} | 📍 {geo_level}")

        print(f"\n📈 SUMMARY:")
        print(f"   Total sources investigated: {total_sources}")
        print(f"   Usable sources: {usable_sources} ({usable_sources/total_sources*100:.1f}%)")
        print(f"   Fully automated: {automated_sources} ({automated_sources/usable_sources*100 if usable_sources else 0:.1f}%)")

        if key_gaps:
            print(f"\n🚫 KEY GAPS:")
            for gap in key_gaps[:3]:  # Top 3
                print(f"   • {gap}")

        print(f"\n🎯 NEXT STEPS:")
        if automated_sources >= 6:
            print("   ✅ Sufficient automated data sources identified")
        else:
            print("   ⚠️  May need additional research for automated sources")

        # Data collection strategy
        strategy = {
            'crop_yields': 'World Bank + FAOSTAT (need state-level breakdown)',
            'climate': 'Open-Meteo (current) + NASA POWER (historical) + ERA5 (premium)',
            'soil': 'SoilGrids API',
            'boundaries': 'GADM + OSM boundaries',
            'irrigation': 'GEM maps + government open data'
        }

        print("\n🔧 RECOMMENDED COLLECTION STRATEGY:")
        for data_type, sources in strategy.items():
            print(f"   • {data_type.upper()}: {sources}")

    def save_research_results(self):
        """Save comprehensive research results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/research/data_sources_research_{timestamp}.json"

        research_summary = {
            'timestamp': timestamp,
            'target_region': self.target_states,
            'target_crops': self.crops,
            'research_results': self.data_sources,
            'summary': {
                'total_sources': sum(len(sources) for sources in self.data_sources.values()),
                'available_sources': sum(1 for sources in self.data_sources.values()
                                       for source in sources.values() if (isinstance(source, dict) and source.get('available')) or (isinstance(source, bool) and source)),
                'automated_sources': sum(1 for sources in self.data_sources.values()
                                       for source in sources.values() if
                                       ((isinstance(source, dict) and source.get('available') and
                                         source.get('automated', source.get('automated_access', False))) or
                                        (isinstance(source, bool) and source)))
            }
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(research_summary, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Research results saved to: {filename}")

        # Save human-readable summary
        summary_file = f"data/research/data_sources_summary_{timestamp}.txt"
        with open(summary_file, 'w') as f:
            f.write("NORTH INDIA CROP PREDICTION - DATA SOURCES RESEARCH\n")
            f.write("="*55 + "\n\n")
            f.write(f"Research Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Target States: {', '.join(self.target_states)}\n")
            f.write(f"Target Crops: {', '.join(self.crops)}\n\n")

            total_sources = research_summary['summary']['total_sources']
            available = research_summary['summary']['available_sources']
            automated = research_summary['summary']['automated_sources']

            f.write(f"SOURCES SUMMARY:\n")
            f.write(f"- Total investigated: {total_sources}\n")
            f.write(f"- Available: {available} ({available/total_sources*100:.1f}%)\n")
            f.write(f"- Automated: {automated} ({automated/available*100 if available else 0:.1f}%)\n\n")

            for category, sources in self.data_sources.items():
                f.write(f"{category.upper().replace('_', ' ')}:\n")
                for name, info in sources.items():
                    available = info.get('available') if isinstance(info, dict) else bool(info)
                    status = "✅ AVAILABLE" if available else "❌ UNAVAILABLE"
                    f.write(f"  {status} {name}\n")
                    if available and isinstance(info, dict):
                        if 'temporal_coverage' in info:
                            f.write(f"    Temporal: {info['temporal_coverage']}\n")
                        if 'geographical_level' in info:
                            f.write(f"    Geo Level: {info['geographical_level']}\n")
                f.write("\n")

        print(f"📄 Summary saved to: {summary_file}")


def main():
    """Main research function"""
    print("🚀 NORTH INDIA CROP PREDICTION - PHASE 1: DATA SOURCES RESEARCH")
    print("Target: Punjab, Haryana, UP, Bihar, MP | Crops: Rice, Wheat, Maize")
    print("Requirement: Fully automated, open source data sources\n")

    researcher = DataSourceResearcher()

    # Research all data sources
    researcher.research_world_bank_data()
    researcher.research_faostat_data()
    researcher.research_indian_government_data()
    researcher.research_climate_data_sources()
    researcher.research_geospatial_data()
    researcher.research_agricultural_zones()

    # Generate summary and save results
    researcher.generate_data_requirements_summary()
    researcher.save_research_results()

    print("\n✅ Phase 1 Research Complete!")
    print("📁 Check 'data/research/' folder for detailed results")


if __name__ == "__main__":
    main()
