#!/usr/bin/env python3
"""
Looker Cache Population CLI Script

This script populates the database cache with ALL models, explores, and dashboards
from your Looker instance. Run this daily to ensure complete data coverage.

Usage:
    python populate_cache.py [--models] [--explores] [--dashboards] [--all]
    
Options:
    --models        Populate only models cache
    --explores      Populate only explores cache  
    --dashboards    Populate only dashboards cache
    --all           Populate all caches (default)
    --force         Force refresh even if cache is fresh
    --verbose       Enable verbose logging
    --help          Show this help message

Environment Variables:
    The script automatically loads variables from .env file if present.
    Required variables: LOOKER_BASE_URL, LOOKER_CLIENT_ID, LOOKER_CLIENT_SECRET, OPENAI_API_KEY
    
    Example .env file:
    LOOKER_BASE_URL=https://your-company.cloud.looker.com
    LOOKER_CLIENT_ID=your_client_id
    LOOKER_CLIENT_SECRET=your_client_secret
    OPENAI_API_KEY=sk-your_openai_key
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Load environment variables from .env file
from dotenv import load_dotenv

# Add the app directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv()

def setup_logging(verbose: bool = False):
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

class LookerCachePopulator:
    """Comprehensive cache populator for Looker data"""
    
    def __init__(self, verbose: bool = False):
        """Initialize the cache populator"""
        self.verbose = verbose
        self.stats = {
            'models_cached': 0,
            'explores_cached': 0,
            'dashboards_cached': 0,
            'start_time': datetime.now()
        }
        
        # Initialize components
        self._init_database()
        self._init_looker_agent()
    
    def _init_database(self):
        """Initialize database connection"""
        try:
            from app import app, db
            self.app = app
            self.db = db
            
            # Create app context for database operations
            self.app_context = self.app.app_context()
            self.app_context.push()
            
            # Ensure all tables exist
            self.db.create_all()
            logging.info("Database initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize database: {e}")
            raise
    
    def _init_looker_agent(self):
        """Initialize Looker agent for API operations"""
        try:
            from chat_agent import LookerChatAgent
            self.agent = LookerChatAgent()
            
            if not self.agent.credentials_available:
                raise ValueError("Looker credentials not available")
            
            # Test connection
            if not self.agent.test_connection():
                raise ValueError("Looker connection test failed")
                
            logging.info(f"Looker agent initialized successfully for instance: {self.agent.looker_base_url}")
            
        except Exception as e:
            logging.error(f"Failed to initialize Looker agent: {e}")
            raise
    
    def populate_models(self, force: bool = False) -> int:
        """Populate models cache with ALL available models"""
        try:
            logging.info("Starting models cache population...")
            
            # Check if we need to refresh
            if not force and self._is_models_cache_fresh():
                logging.info("Models cache is fresh, skipping refresh")
                return 0
            
            # Get all models from Looker API
            logging.info("Fetching all models from Looker API...")
            models = self.agent.sdk.all_lookml_models()
            
            if not models:
                logging.warning("No models found in Looker instance")
                return 0
            
            # Clear existing models for this instance
            from models import LookerModel
            deleted_count = LookerModel.query.filter(
                LookerModel.looker_instance_id == self.agent.looker_instance_id
            ).delete()
            logging.info(f"Cleared {deleted_count} existing model records")
            
            # Process all models
            models_data = []
            for model in models:
                model_info = {
                    'name': model.name,
                    'project_name': getattr(model, 'project_name', ''),
                    'label': getattr(model, 'label', model.name),
                    'description': getattr(model, 'description', '')
                }
                models_data.append(model_info)
                
                # Create database record
                db_model = LookerModel(
                    looker_instance_id=self.agent.looker_instance_id,
                    model_name=model.name,
                    project_name=getattr(model, 'project_name', None),
                    label=getattr(model, 'label', None),
                    description=getattr(model, 'description', None),
                    model_metadata=model_info
                )
                self.db.session.add(db_model)
                
                if self.verbose:
                    logging.debug(f"Cached model: {model.name}")
            
            # Commit all models
            self.db.session.commit()
            self.stats['models_cached'] = len(models_data)
            
            logging.info(f"Successfully cached {len(models_data)} models")
            return len(models_data)
            
        except Exception as e:
            logging.error(f"Error populating models cache: {e}")
            self.db.session.rollback()
            raise
    
    def populate_explores(self, force: bool = False) -> int:
        """Populate explores cache with ALL available explores from all models"""
        try:
            logging.info("Starting explores cache population...")
            
            # Check if we need to refresh
            if not force and self._is_explores_cache_fresh():
                logging.info("Explores cache is fresh, skipping refresh")
                return 0
            
            # Get all models to iterate through their explores
            from models import LookerModel
            models = LookerModel.query.filter(
                LookerModel.looker_instance_id == self.agent.looker_instance_id
            ).all()
            
            if not models:
                logging.warning("No models found in cache. Run models population first.")
                return 0
            
            # Clear existing explores for this instance
            from models import LookerExplore
            deleted_count = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == self.agent.looker_instance_id
            ).delete()
            logging.info(f"Cleared {deleted_count} existing explore records")
            
            total_explores = 0
            
            for model in models:
                try:
                    logging.info(f"Processing explores for model: {model.model_name}")
                    
                    # Get model info with explores
                    model_info = self.agent.sdk.lookml_model(model.model_name)
                    
                    if not hasattr(model_info, 'explores') or not model_info.explores:
                        logging.debug(f"No explores found in model {model.model_name}")
                        continue
                    
                    model_explore_count = 0
                    
                    for explore in model_info.explores:
                        if not explore.name:
                            continue
                            
                        try:
                            # Get comprehensive explore metadata
                            explore_metadata = self.agent._fetch_explore_metadata(
                                model.model_name, 
                                explore.name
                            )
                            
                            # Create database record
                            db_explore = LookerExplore(
                                looker_instance_id=self.agent.looker_instance_id,
                                model_name=model.model_name,
                                explore_name=explore.name,
                                label=explore_metadata.get('label', explore.name),
                                description=explore_metadata.get('description', ''),
                                dimensions=explore_metadata.get('dimensions', []),
                                measures=explore_metadata.get('measures', []),
                                explore_metadata=explore_metadata
                            )
                            self.db.session.add(db_explore)
                            
                            model_explore_count += 1
                            total_explores += 1
                            
                            if self.verbose:
                                logging.debug(f"Cached explore: {model.model_name}.{explore.name}")
                                
                        except Exception as explore_error:
                            logging.warning(f"Failed to cache explore {model.model_name}.{explore.name}: {explore_error}")
                            continue
                    
                    logging.info(f"Cached {model_explore_count} explores for model {model.model_name}")
                    
                    # Commit periodically to avoid memory issues
                    if total_explores % 50 == 0:
                        self.db.session.commit()
                        logging.debug(f"Intermediate commit at {total_explores} explores")
                    
                except Exception as model_error:
                    logging.error(f"Error processing model {model.model_name}: {model_error}")
                    continue
            
            # Final commit
            self.db.session.commit()
            self.stats['explores_cached'] = total_explores
            
            logging.info(f"Successfully cached {total_explores} explores across all models")
            return total_explores
            
        except Exception as e:
            logging.error(f"Error populating explores cache: {e}")
            self.db.session.rollback()
            raise
    
    def populate_dashboards(self, force: bool = False) -> int:
        """Populate dashboards cache with ALL available dashboards"""
        try:
            logging.info("Starting dashboards cache population...")
            
            # Check if we need to refresh
            if not force and self._is_dashboards_cache_fresh():
                logging.info("Dashboards cache is fresh, skipping refresh")
                return 0
            
            # Get ALL dashboards from Looker API (no limit!)
            logging.info("Fetching ALL dashboards from Looker API (no limit)...")
            
            # Clear existing dashboards for this instance
            from models import LookerDashboard, DashboardExploreMapping
            
            deleted_dashboards = LookerDashboard.query.filter(
                LookerDashboard.looker_instance_id == self.agent.looker_instance_id
            ).delete()
            
            deleted_mappings = DashboardExploreMapping.query.filter(
                DashboardExploreMapping.looker_instance_id == self.agent.looker_instance_id
            ).delete()
            
            logging.info(f"Cleared {deleted_dashboards} dashboard records and {deleted_mappings} mapping records")
            
            # Fetch dashboards in batches to handle large numbers
            dashboards = self.agent.sdk.all_dashboards(
                fields='id,title,description,folder,tags,updated_at,view_count,space,dashboard_filters,dashboard_elements'
            )
            
            if not dashboards:
                logging.warning("No dashboards found in Looker instance")
                return 0
            
            logging.info(f"Found {len(dashboards)} dashboards to process")
            
            dashboard_count = 0
            mapping_count = 0
            
            for i, dashboard in enumerate(dashboards):
                try:
                    if not dashboard.id:
                        continue
                    
                    # Extract folder information
                    folder_name = ""
                    if hasattr(dashboard, 'folder') and dashboard.folder:
                        if hasattr(dashboard.folder, 'name'):
                            folder_name = dashboard.folder.name
                        elif isinstance(dashboard.folder, dict):
                            folder_name = dashboard.folder.get('name', '')
                    
                    # Extract space information as fallback
                    if not folder_name and hasattr(dashboard, 'space') and dashboard.space:
                        if hasattr(dashboard.space, 'name'):
                            folder_name = dashboard.space.name
                        elif isinstance(dashboard.space, dict):
                            folder_name = dashboard.space.get('name', '')
                    
                    # Get detailed dashboard info
                    try:
                        detailed_info = self.agent._fetch_detailed_dashboard_info(dashboard.id)
                    except Exception as detail_error:
                        logging.warning(f"Could not fetch detailed info for dashboard {dashboard.id}: {detail_error}")
                        detailed_info = {
                            'elements': [],
                            'explore_references': [],
                            'lookml_references': [],
                            'usage_counts': {},
                            'tags': []
                        }
                    
                    # Create dashboard record
                    db_dashboard = LookerDashboard(
                        looker_instance_id=self.agent.looker_instance_id,
                        dashboard_id=dashboard.id,
                        title=getattr(dashboard, 'title', '') or f"Dashboard {dashboard.id}",
                        description=getattr(dashboard, 'description', ''),
                        folder_name=folder_name,
                        tags=detailed_info.get('tags', []),
                        dashboard_elements=detailed_info.get('elements', []),
                        explore_references=detailed_info.get('explore_references', []),
                        lookml_references=detailed_info.get('lookml_references', []),
                        user_access_count=getattr(dashboard, 'view_count', 0),
                    )
                    self.db.session.add(db_dashboard)
                    dashboard_count += 1
                    
                    # Create dashboard-to-explore mappings
                    for explore_ref in detailed_info.get('explore_references', []):
                        if '.' in explore_ref:
                            model_name, explore_name = explore_ref.split('.', 1)
                            mapping = DashboardExploreMapping(
                                looker_instance_id=self.agent.looker_instance_id,
                                dashboard_id=dashboard.id,
                                model_name=model_name,
                                explore_name=explore_name,
                                usage_count=detailed_info.get('usage_counts', {}).get(explore_ref, 1),
                                business_context_score=self.agent._calculate_business_context_score(
                                    {
                                        'title': getattr(dashboard, 'title', ''),
                                        'description': getattr(dashboard, 'description', ''),
                                        'folder': folder_name,
                                        'view_count': getattr(dashboard, 'view_count', 0)
                                    }, 
                                    explore_ref
                                )
                            )
                            self.db.session.add(mapping)
                            mapping_count += 1
                    
                    # Log progress for important dashboards
                    title = getattr(dashboard, 'title', '')
                    if dashboard.id == '2659' or any(keyword in title.lower() for keyword in ['bi', 'cost', 'weekly']):
                        logging.info(f"Cached important dashboard - ID: {dashboard.id}, Title: '{title}', Folder: '{folder_name}'")
                    
                    if self.verbose:
                        logging.debug(f"Cached dashboard {dashboard.id}: {title}")
                    
                    # Commit periodically for large datasets
                    if dashboard_count % 100 == 0:
                        self.db.session.commit()
                        logging.info(f"Intermediate commit: {dashboard_count} dashboards, {mapping_count} mappings processed")
                        
                except Exception as dash_error:
                    logging.error(f"Error processing dashboard {dashboard.id}: {dash_error}")
                    continue
            
            # Final commit
            self.db.session.commit()
            self.stats['dashboards_cached'] = dashboard_count
            
            logging.info(f"Successfully cached {dashboard_count} dashboards and {mapping_count} explore mappings")
            return dashboard_count
            
        except Exception as e:
            logging.error(f"Error populating dashboards cache: {e}")
            self.db.session.rollback()
            raise
    
    def _is_models_cache_fresh(self) -> bool:
        """Check if models cache is fresh (within 24 hours)"""
        try:
            from models import LookerModel
            from datetime import timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            fresh_models = LookerModel.query.filter(
                LookerModel.looker_instance_id == self.agent.looker_instance_id,
                LookerModel.updated_at > cutoff_time
            ).count()
            
            return fresh_models > 0
        except Exception:
            return False
    
    def _is_explores_cache_fresh(self) -> bool:
        """Check if explores cache is fresh (within 24 hours)"""
        try:
            from models import LookerExplore
            from datetime import timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            fresh_explores = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == self.agent.looker_instance_id,
                LookerExplore.updated_at > cutoff_time
            ).count()
            
            return fresh_explores > 0
        except Exception:
            return False
    
    def _is_dashboards_cache_fresh(self) -> bool:
        """Check if dashboards cache is fresh (within 24 hours)"""
        try:
            from models import LookerDashboard
            from datetime import timedelta
            
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            fresh_dashboards = LookerDashboard.query.filter(
                LookerDashboard.looker_instance_id == self.agent.looker_instance_id,
                LookerDashboard.updated_at > cutoff_time
            ).count()
            
            return fresh_dashboards > 0
        except Exception:
            return False
    
    def populate_all(self, force: bool = False) -> Dict[str, int]:
        """Populate all caches (models, explores, dashboards)"""
        results = {}
        
        try:
            # Populate in dependency order
            logging.info("Starting comprehensive cache population...")
            
            results['models'] = self.populate_models(force)
            results['explores'] = self.populate_explores(force)  
            results['dashboards'] = self.populate_dashboards(force)
            
            return results
            
        except Exception as e:
            logging.error(f"Error in comprehensive cache population: {e}")
            raise
    
    def print_summary(self):
        """Print summary statistics"""
        duration = datetime.now() - self.stats['start_time']
        
        print("\n" + "="*50)
        print("LOOKER CACHE POPULATION SUMMARY")
        print("="*50)
        print(f"Looker Instance: {self.agent.looker_base_url}")
        print(f"Duration: {duration}")
        print(f"Models Cached: {self.stats['models_cached']}")
        print(f"Explores Cached: {self.stats['explores_cached']}")
        print(f"Dashboards Cached: {self.stats['dashboards_cached']}")
        print("="*50)
        
        if self.stats['dashboards_cached'] > 100:
            print(f"✅ SUCCESS: Cached {self.stats['dashboards_cached']} dashboards")
            print("   This should now include dashboards beyond the previous 100-limit!")
        
        print("\n💡 Next steps:")
        print("   - Your chatbot will now have access to ALL dashboards")
        print("   - Dashboard queries should find relevant results more accurately")
        print("   - Consider running this script daily via cron for fresh data")
    
    def cleanup(self):
        """Clean up resources"""
        if hasattr(self, 'app_context'):
            self.app_context.pop()

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Populate Looker cache with comprehensive data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--models', action='store_true', 
                       help='Populate only models cache')
    parser.add_argument('--explores', action='store_true',
                       help='Populate only explores cache')
    parser.add_argument('--dashboards', action='store_true',
                       help='Populate only dashboards cache') 
    parser.add_argument('--all', action='store_true',
                       help='Populate all caches (default)')
    parser.add_argument('--force', action='store_true',
                       help='Force refresh even if cache is fresh')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Default to --all if no specific cache type is specified
    if not any([args.models, args.explores, args.dashboards]):
        args.all = True
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Check if .env file exists and log the status
    env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file_path):
        logging.info(f"✅ Loaded environment variables from: {env_file_path}")
    else:
        logging.warning("⚠️ No .env file found. Using system environment variables only.")
    
    # Check environment variables
    required_vars = ['LOOKER_BASE_URL', 'LOOKER_CLIENT_ID', 'LOOKER_CLIENT_SECRET', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logging.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        if os.path.exists(env_file_path):
            logging.error("💡 Check your .env file to ensure these variables are properly set")
        else:
            logging.error("💡 Create a .env file with the required variables or set them in your system environment")
        sys.exit(1)
    
    # Log successful environment setup
    looker_url = os.getenv('LOOKER_BASE_URL')
    logging.info(f"🔗 Looker Instance: {looker_url}")
    logging.info(f"🔑 Environment variables loaded successfully")
    
    populator = None
    try:
        # Initialize cache populator
        logging.info("Initializing Looker cache populator...")
        populator = LookerCachePopulator(verbose=args.verbose)
        
        # Execute requested operations
        if args.all:
            results = populator.populate_all(args.force)
            logging.info(f"Cache population completed: {results}")
        else:
            if args.models:
                count = populator.populate_models(args.force)
                logging.info(f"Models cache population completed: {count} models")
            
            if args.explores:  
                count = populator.populate_explores(args.force)
                logging.info(f"Explores cache population completed: {count} explores")
            
            if args.dashboards:
                count = populator.populate_dashboards(args.force)
                logging.info(f"Dashboards cache population completed: {count} dashboards")
        
        # Print summary
        populator.print_summary()
        
    except KeyboardInterrupt:
        logging.info("Cache population interrupted by user")
        sys.exit(1)
        
    except Exception as e:
        logging.error(f"Cache population failed: {e}")
        sys.exit(1)
        
    finally:
        if populator:
            populator.cleanup()

if __name__ == '__main__':
    main()