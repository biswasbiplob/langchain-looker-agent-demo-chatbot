import os
import logging
import hashlib
from typing import List, Dict, Any, Optional
import looker_sdk
from datetime import datetime, timedelta

class LookerChatAgent:
    """Chat agent that integrates with Looker BI using looker_sdk directly"""
    
    def __init__(self):
        """Initialize the Looker agent with environment variables"""
        self.looker_base_url = os.getenv('LOOKER_BASE_URL')
        self.looker_client_id = os.getenv('LOOKER_CLIENT_ID')
        self.looker_client_secret = os.getenv('LOOKER_CLIENT_SECRET')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.lookml_model_name = os.getenv('LOOKML_MODEL_NAME')
        self.jdbc_driver_path = os.getenv('JDBC_DRIVER_PATH')
        
        # Check if we have the minimum required credentials (removed LOOKML_MODEL_NAME requirement)
        self.credentials_available = bool(
            self.looker_base_url and 
            self.looker_client_id and 
            self.looker_client_secret and 
            self.openai_api_key
        )
        
        self.sdk = None
        self.llm = None
        
        # Create unique instance ID based on Looker URL for database caching
        self.looker_instance_id = hashlib.md5(
            self.looker_base_url.encode('utf-8') if self.looker_base_url else b'default'
        ).hexdigest()
        
        # Cache refresh interval (24 hours)
        self.cache_refresh_hours = 24
        
        # Dashboard cache (will be populated on first request)
        self.dashboards_cache = None
        
        if self.credentials_available:
            try:
                self._initialize_agent()
            except Exception as e:
                logging.error(f"Failed to initialize Looker agent: {e}")
                self.credentials_available = False
        
    def _initialize_agent(self):
        """Initialize the Looker SDK agent"""
        try:
            # Set up environment variables for Looker SDK
            os.environ['LOOKERSDK_BASE_URL'] = self.looker_base_url
            os.environ['LOOKERSDK_CLIENT_ID'] = self.looker_client_id
            os.environ['LOOKERSDK_CLIENT_SECRET'] = self.looker_client_secret
            
            # Initialize Looker SDK
            self.sdk = looker_sdk.init40()
            
            # Initialize OpenAI for natural language processing
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                api_key=self.openai_api_key,
                temperature=0,
                model="gpt-4o",
                max_tokens=2000
            )
            
            # Test connection
            user = self.sdk.me()
            logging.info(f"Looker SDK initialized successfully for user: {user.display_name}")
            
            # In-memory cache (kept for backward compatibility)
            self.models_cache = None
            self.explores_cache = {}
            self.model_explores_cache = {}
            
        except Exception as e:
            logging.error(f"Failed to initialize Looker SDK agent: {e}")
            raise
    
    def _is_cache_fresh(self, created_at: datetime) -> bool:
        """Check if cached data is still fresh"""
        if not created_at:
            return False
        cache_expiry = created_at + timedelta(hours=self.cache_refresh_hours)
        return datetime.utcnow() < cache_expiry
    
    def _get_db_models(self) -> List[Dict[str, Any]]:
        """Get models from database cache"""
        try:
            from models import LookerModel
            from app import db
            
            # Get all models for this Looker instance that are fresh
            cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_refresh_hours)
            
            models = LookerModel.query.filter(
                LookerModel.looker_instance_id == self.looker_instance_id,
                LookerModel.updated_at > cutoff_time
            ).all()
            
            if not models:
                return []
            
            # Convert to format expected by existing code
            model_list = []
            for model in models:
                model_info = {
                    'name': model.model_name,
                    'project_name': model.project_name or '',
                    'label': model.label or model.model_name,
                    'description': model.description or ''
                }
                model_list.append(model_info)
            
            logging.info(f"Retrieved {len(model_list)} models from database cache")
            return model_list
            
        except Exception as e:
            logging.error(f"Error retrieving models from database: {e}")
            return []
    
    def _save_models_to_db(self, models_data: List[Dict[str, Any]]) -> None:
        """Save models to database cache"""
        try:
            from models import LookerModel
            from app import db
            
            # First, clear existing models for this instance
            LookerModel.query.filter(
                LookerModel.looker_instance_id == self.looker_instance_id
            ).delete()
            
            # Add new models
            for model_data in models_data:
                db_model = LookerModel(
                    looker_instance_id=self.looker_instance_id,
                    model_name=model_data['name'],
                    project_name=model_data.get('project_name'),
                    label=model_data.get('label'),
                    description=model_data.get('description'),
                    model_metadata=model_data  # Store full metadata as JSON
                )
                db.session.add(db_model)
            
            db.session.commit()
            logging.info(f"Saved {len(models_data)} models to database cache")
            
        except Exception as e:
            logging.error(f"Error saving models to database: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def _get_db_explores(self, model_name: str = None) -> List[Dict[str, Any]]:
        """Get explores from database cache"""
        try:
            from models import LookerExplore
            from app import db
            
            # Get all explores for this Looker instance that are fresh
            cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_refresh_hours)
            
            query = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == self.looker_instance_id,
                LookerExplore.updated_at > cutoff_time
            )
            
            if model_name:
                query = query.filter(LookerExplore.model_name == model_name)
            
            explores = query.all()
            
            if not explores:
                return []
            
            # Convert to format expected by existing code
            explore_list = []
            for explore in explores:
                if model_name:
                    # Return just explore names for specific model
                    explore_list.append(explore.explore_name)
                else:
                    # Return model.explore format for all explores
                    explore_list.append(f"{explore.model_name}.{explore.explore_name}")
            
            logging.info(f"Retrieved {len(explore_list)} explores from database cache")
            return explore_list
            
        except Exception as e:
            logging.error(f"Error retrieving explores from database: {e}")
            return []
    
    def _save_explores_to_db(self, model_name: str, explores_data: List[str]) -> None:
        """Save explores to database cache with enhanced metadata collection"""
        try:
            from models import LookerExplore
            from app import db
            
            # First, clear existing explores for this model
            LookerExplore.query.filter(
                LookerExplore.looker_instance_id == self.looker_instance_id,
                LookerExplore.model_name == model_name
            ).delete()
            
            # Add new explores with basic metadata
            for explore_name in explores_data:
                # Try to get basic explore info immediately for better caching
                try:
                    explore_info = self._fetch_explore_metadata(model_name, explore_name)
                    
                    db_explore = LookerExplore(
                        looker_instance_id=self.looker_instance_id,
                        model_name=model_name,
                        explore_name=explore_name,
                        label=explore_info.get('label', explore_name),
                        description=explore_info.get('description', f"Data from the {explore_name} explore in {model_name} model"),
                        dimensions=explore_info.get('dimensions', []),
                        measures=explore_info.get('measures', []),
                        explore_metadata=explore_info
                    )
                except Exception as detail_error:
                    logging.warning(f"Could not fetch detailed metadata for {model_name}.{explore_name}: {detail_error}")
                    # Fall back to basic info
                    db_explore = LookerExplore(
                        looker_instance_id=self.looker_instance_id,
                        model_name=model_name,
                        explore_name=explore_name,
                        label=explore_name,
                        description=f"Data from the {explore_name} explore in {model_name} model",
                        dimensions=[],  # Will be populated when detailed info is requested
                        measures=[],
                        explore_metadata={}
                    )
                
                db.session.add(db_explore)
            
            db.session.commit()
            logging.info(f"Saved {len(explores_data)} explores for model {model_name} to database cache with enhanced metadata")
            
        except Exception as e:
            logging.error(f"Error saving explores to database: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def _fetch_explore_metadata(self, model_name: str, explore_name: str) -> Dict[str, Any]:
        """Fetch comprehensive explore metadata from Looker API"""
        try:
            # Get explore metadata with field information
            explore = self.sdk.lookml_model_explore(
                lookml_model_name=model_name,
                explore_name=explore_name
            )
            
            explore_info = {
                'name': explore.name,
                'label': getattr(explore, 'label', explore.name),
                'description': getattr(explore, 'description', ''),
                'dimensions': [],
                'measures': [],
                'field_keywords': []  # New: keywords extracted from field names
            }
            
            # Extract field information with more details
            field_keywords = []
            
            if hasattr(explore, 'fields') and explore.fields:
                if hasattr(explore.fields, 'dimensions') and explore.fields.dimensions:
                    for d in explore.fields.dimensions:
                        if not d.name:
                            continue
                        
                        dimension_info = {
                            'name': d.name,
                            'label': getattr(d, 'label', d.name),
                            'description': getattr(d, 'description', ''),
                            'type': getattr(d, 'type', ''),
                            'tags': getattr(d, 'tags', [])
                        }
                        explore_info['dimensions'].append(dimension_info)
                        
                        # Extract keywords from field names and descriptions
                        field_keywords.extend(self._extract_keywords(d.name, dimension_info['label'], dimension_info['description']))
                
                if hasattr(explore.fields, 'measures') and explore.fields.measures:
                    for m in explore.fields.measures:
                        if not m.name:
                            continue
                            
                        measure_info = {
                            'name': m.name,
                            'label': getattr(m, 'label', m.name),
                            'description': getattr(m, 'description', ''),
                            'type': getattr(m, 'type', ''),
                            'tags': getattr(m, 'tags', [])
                        }
                        explore_info['measures'].append(measure_info)
                        
                        # Extract keywords from field names and descriptions
                        field_keywords.extend(self._extract_keywords(m.name, measure_info['label'], measure_info['description']))
            
            # Store unique keywords for semantic matching
            explore_info['field_keywords'] = list(set(field_keywords))
            
            return explore_info
            
        except Exception as e:
            logging.warning(f"Error fetching explore metadata for {model_name}.{explore_name}: {e}")
            return {
                'name': explore_name,
                'label': explore_name,
                'description': '',
                'dimensions': [],
                'measures': [],
                'field_keywords': []
            }
    
    def _extract_keywords(self, field_name: str, label: str, description: str) -> List[str]:
        """Extract relevant keywords from field names, labels, and descriptions"""
        import re
        
        keywords = []
        
        # Process field name
        if field_name:
            # Split camelCase and snake_case
            field_parts = re.findall(r'[A-Z][a-z]+|[a-z]+|[0-9]+', field_name.replace('_', ' '))
            keywords.extend([part.lower() for part in field_parts if len(part) > 2])
        
        # Process label
        if label and label != field_name:
            label_parts = re.findall(r'\b\w+\b', label.lower())
            keywords.extend([part for part in label_parts if len(part) > 2])
        
        # Process description
        if description:
            desc_parts = re.findall(r'\b\w+\b', description.lower())
            # Only take meaningful words (length > 3) and limit to avoid noise
            keywords.extend([part for part in desc_parts if len(part) > 3][:5])
        
        return keywords
    
    def _get_detailed_explore_info(self, model_name: str, explore_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed explore info from database cache"""
        try:
            from models import LookerExplore
            from app import db
            
            cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_refresh_hours)
            
            explore = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == self.looker_instance_id,
                LookerExplore.model_name == model_name,
                LookerExplore.explore_name == explore_name,
                LookerExplore.updated_at > cutoff_time
            ).first()
            
            if not explore or not explore.dimensions:  # No detailed info cached yet
                return None
            
            # Convert from database format to expected format
            explore_info = {
                'name': explore.explore_name,
                'model': explore.model_name,
                'description': explore.description or f"Data from the {explore_name} explore in {model_name} model",
                'dimensions': explore.dimensions or [],
                'measures': explore.measures or []
            }
            
            logging.info(f"Retrieved detailed explore info for {model_name}.{explore_name} from database cache")
            return explore_info
            
        except Exception as e:
            logging.error(f"Error retrieving detailed explore info from database: {e}")
            return None
    
    def _save_detailed_explore_info(self, model_name: str, explore_name: str, explore_info: Dict[str, Any]) -> None:
        """Save detailed explore info to database cache"""
        try:
            from models import LookerExplore
            from app import db
            
            # Find existing explore record or create new one
            explore_record = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == self.looker_instance_id,
                LookerExplore.model_name == model_name,
                LookerExplore.explore_name == explore_name
            ).first()
            
            if explore_record:
                # Update existing record with detailed info
                explore_record.description = explore_info['description']
                explore_record.dimensions = explore_info['dimensions']
                explore_record.measures = explore_info['measures']
                explore_record.explore_metadata = explore_info
                explore_record.updated_at = datetime.utcnow()
            else:
                # Create new record
                explore_record = LookerExplore(
                    looker_instance_id=self.looker_instance_id,
                    model_name=model_name,
                    explore_name=explore_name,
                    label=explore_info.get('name', explore_name),
                    description=explore_info['description'],
                    dimensions=explore_info['dimensions'],
                    measures=explore_info['measures'],
                    explore_metadata=explore_info
                )
                db.session.add(explore_record)
            
            db.session.commit()
            logging.info(f"Saved detailed explore info for {model_name}.{explore_name} to database cache")
            
        except Exception as e:
            logging.error(f"Error saving detailed explore info to database: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def get_available_dashboards(self) -> List[Dict[str, Any]]:
        """Get list of available dashboards with business context"""
        try:
            if not hasattr(self, 'sdk') or not self.sdk:
                return []
            
            # First try to get from database cache
            db_dashboards = self._get_db_dashboards()
            if db_dashboards:
                self.dashboards_cache = db_dashboards
                return db_dashboards
            
            # If no fresh database cache, fetch from Looker API
            logging.info("Fetching dashboards from Looker API...")
            dashboards = self.sdk.all_dashboards(fields='id,title,description,folder,updated_at,view_count')
            dashboard_list = []
            
            for dashboard in dashboards[:50]:  # Limit to prevent overwhelming API
                if not dashboard.id:
                    continue
                    
                dashboard_info = {
                    'id': dashboard.id,
                    'title': getattr(dashboard, 'title', ''),
                    'description': getattr(dashboard, 'description', ''),
                    'folder': getattr(dashboard, 'folder', {}).get('name', '') if hasattr(dashboard, 'folder') and dashboard.folder else '',
                    'view_count': getattr(dashboard, 'view_count', 0),
                    'updated_at': getattr(dashboard, 'updated_at', ''),
                    'explore_references': [],  # Will be populated when detailed info is fetched
                }
                dashboard_list.append(dashboard_info)
            
            # Save to database cache for next time
            if dashboard_list:
                self._save_dashboards_to_db(dashboard_list)
            
            # Cache in memory
            self.dashboards_cache = dashboard_list
            return dashboard_list
            
        except Exception as e:
            logging.error(f"Error getting dashboards: {e}")
            return []
    
    def _get_db_dashboards(self) -> List[Dict[str, Any]]:
        """Get dashboards from database cache"""
        try:
            from models import LookerDashboard
            from app import db
            
            # Get all dashboards for this Looker instance that are fresh
            cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_refresh_hours)
            
            dashboards = LookerDashboard.query.filter(
                LookerDashboard.looker_instance_id == self.looker_instance_id,
                LookerDashboard.updated_at > cutoff_time
            ).all()
            
            if not dashboards:
                return []
            
            # Convert to format expected by existing code
            dashboard_list = []
            for dashboard in dashboards:
                dashboard_info = {
                    'id': dashboard.dashboard_id,
                    'title': dashboard.title or '',
                    'description': dashboard.description or '',
                    'folder': dashboard.folder_name or '',
                    'view_count': dashboard.user_access_count or 0,
                    'explore_references': dashboard.explore_references or [],
                    'tags': dashboard.tags or []
                }
                dashboard_list.append(dashboard_info)
            
            logging.info(f"Retrieved {len(dashboard_list)} dashboards from database cache")
            return dashboard_list
            
        except Exception as e:
            logging.error(f"Error retrieving dashboards from database: {e}")
            return []
    
    def _save_dashboards_to_db(self, dashboards_data: List[Dict[str, Any]]) -> None:
        """Save dashboards to database cache with enhanced metadata"""
        try:
            from models import LookerDashboard, DashboardExploreMapping
            from app import db
            
            # First, clear existing dashboards for this instance
            LookerDashboard.query.filter(
                LookerDashboard.looker_instance_id == self.looker_instance_id
            ).delete()
            
            # Clear existing mappings
            DashboardExploreMapping.query.filter(
                DashboardExploreMapping.looker_instance_id == self.looker_instance_id
            ).delete()
            
            # Add new dashboards with detailed metadata
            for dashboard_data in dashboards_data:
                try:
                    # Get detailed dashboard info including elements
                    detailed_info = self._fetch_detailed_dashboard_info(dashboard_data['id'])
                    
                    db_dashboard = LookerDashboard(
                        looker_instance_id=self.looker_instance_id,
                        dashboard_id=dashboard_data['id'],
                        title=dashboard_data.get('title', ''),
                        description=dashboard_data.get('description', ''),
                        folder_name=dashboard_data.get('folder', ''),
                        tags=detailed_info.get('tags', []),
                        dashboard_elements=detailed_info.get('elements', []),
                        explore_references=detailed_info.get('explore_references', []),
                        lookml_references=detailed_info.get('lookml_references', []),
                        user_access_count=dashboard_data.get('view_count', 0),
                    )
                    db.session.add(db_dashboard)
                    
                    # Create dashboard-to-explore mappings for business context
                    for explore_ref in detailed_info.get('explore_references', []):
                        if '.' in explore_ref:
                            model_name, explore_name = explore_ref.split('.', 1)
                            mapping = DashboardExploreMapping(
                                looker_instance_id=self.looker_instance_id,
                                dashboard_id=dashboard_data['id'],
                                model_name=model_name,
                                explore_name=explore_name,
                                usage_count=detailed_info.get('usage_counts', {}).get(explore_ref, 1),
                                business_context_score=self._calculate_business_context_score(
                                    dashboard_data, explore_ref
                                )
                            )
                            db.session.add(mapping)
                
                except Exception as detail_error:
                    logging.warning(f"Could not fetch detailed info for dashboard {dashboard_data['id']}: {detail_error}")
                    # Fall back to basic dashboard info
                    db_dashboard = LookerDashboard(
                        looker_instance_id=self.looker_instance_id,
                        dashboard_id=dashboard_data['id'],
                        title=dashboard_data.get('title', ''),
                        description=dashboard_data.get('description', ''),
                        folder_name=dashboard_data.get('folder', ''),
                        user_access_count=dashboard_data.get('view_count', 0),
                        explore_references=[],
                        tags=[]
                    )
                    db.session.add(db_dashboard)
            
            db.session.commit()
            logging.info(f"Saved {len(dashboards_data)} dashboards to database cache with business context")
            
        except Exception as e:
            logging.error(f"Error saving dashboards to database: {e}")
            try:
                db.session.rollback()
            except:
                pass
    
    def _fetch_detailed_dashboard_info(self, dashboard_id: str) -> Dict[str, Any]:
        """Fetch comprehensive dashboard metadata including elements and explore references"""
        try:
            # Get detailed dashboard info with elements
            dashboard = self.sdk.dashboard(
                dashboard_id,
                fields='dashboard_elements,dashboard_filters,title,description,folder'
            )
            
            detailed_info = {
                'elements': [],
                'explore_references': [],
                'lookml_references': [],
                'usage_counts': {},
                'tags': []
            }
            
            explore_refs = set()
            
            # Extract explore references from dashboard elements (tiles)
            if hasattr(dashboard, 'dashboard_elements') and dashboard.dashboard_elements:
                for element in dashboard.dashboard_elements:
                    if not element:
                        continue
                        
                    element_info = {
                        'title': getattr(element, 'title', ''),
                        'type': getattr(element, 'type', ''),
                        'query_id': getattr(element, 'query_id', None)
                    }
                    
                    # Get query details to extract model/explore references
                    if element.query_id:
                        try:
                            query = self.sdk.query(element.query_id)
                            if query.model and query.explore:
                                explore_ref = f"{query.model}.{query.explore}"
                                explore_refs.add(explore_ref)
                                detailed_info['usage_counts'][explore_ref] = detailed_info['usage_counts'].get(explore_ref, 0) + 1
                                
                                element_info['model'] = query.model
                                element_info['explore'] = query.explore
                        except Exception:
                            pass  # Continue if query details can't be fetched
                    
                    detailed_info['elements'].append(element_info)
            
            detailed_info['explore_references'] = list(explore_refs)
            
            return detailed_info
            
        except Exception as e:
            logging.warning(f"Error fetching detailed dashboard info for {dashboard_id}: {e}")
            return {
                'elements': [],
                'explore_references': [],
                'lookml_references': [],
                'usage_counts': {},
                'tags': []
            }
    
    def _calculate_business_context_score(self, dashboard_data: Dict, explore_ref: str) -> float:
        """Calculate business context relevance score for dashboard-explore relationship"""
        score = 1.0
        
        # Boost score based on dashboard title/description quality
        title = dashboard_data.get('title', '').lower()
        description = dashboard_data.get('description', '').lower()
        
        # Business language indicators boost score
        business_terms = ['analysis', 'dashboard', 'report', 'kpi', 'metric', 'performance', 
                         'overview', 'summary', 'insights', 'trends', 'results']
        
        for term in business_terms:
            if term in title or term in description:
                score += 0.2
        
        # Popular dashboards (high view count) get higher scores  
        view_count = dashboard_data.get('view_count', 0)
        if view_count > 100:
            score += 0.5
        elif view_count > 20:
            score += 0.3
        
        return min(score, 3.0)  # Cap at 3.0
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available LookML models"""
        try:
            if not hasattr(self, 'sdk') or not self.sdk:
                return []
            
            # First try to get from database cache
            db_models = self._get_db_models()
            if db_models:
                # Use database cache
                self.models_cache = db_models
                return db_models
            
            # If no fresh database cache, fetch from Looker API
            logging.info("Fetching models from Looker API...")
            models = self.sdk.all_lookml_models()
            model_list = []
            
            for model in models:
                model_info = {
                    'name': model.name,
                    'project_name': getattr(model, 'project_name', ''),
                    'label': getattr(model, 'label', model.name),
                    'description': getattr(model, 'description', '')
                }
                model_list.append(model_info)
            
            # Save to database cache for next time
            self._save_models_to_db(model_list)
            
            # Cache in memory too
            self.models_cache = model_list
            return model_list
            
        except Exception as e:
            logging.error(f"Error getting models: {e}")
            return []
    
    def get_available_explores(self, model_name: str = None) -> List[str]:
        """Get list of available explores for a specific model or all models"""
        try:
            if not hasattr(self, 'sdk') or not self.sdk:
                return []
            
            # If specific model requested
            if model_name:
                # First try database cache
                db_explores = self._get_db_explores(model_name)
                if db_explores:
                    cache_key = f"explores_{model_name}"
                    self.model_explores_cache[cache_key] = db_explores
                    return db_explores
                
                # Fetch from API if not in cache
                logging.info(f"Fetching explores for model {model_name} from Looker API...")
                model_info = self.sdk.lookml_model(model_name)
                if model_info.explores:
                    explores = [e.name for e in model_info.explores if e.name]
                    # Save to database cache
                    self._save_explores_to_db(model_name, explores)
                    # Cache in memory too
                    cache_key = f"explores_{model_name}"
                    self.model_explores_cache[cache_key] = explores
                    return explores
                return []
            
            # Get explores from all models
            # First try database cache for all explores
            db_explores = self._get_db_explores()
            if db_explores:
                return db_explores
            
            # Fetch from API if not cached
            all_explores = []
            models = self.get_available_models()
            
            for model in models:
                try:
                    model_explores = self.get_available_explores(model['name'])
                    # Prefix with model name for clarity when showing all
                    prefixed_explores = [f"{model['name']}.{explore}" for explore in model_explores]
                    all_explores.extend(prefixed_explores)
                except Exception as e:
                    logging.warning(f"Could not get explores for model {model['name']}: {e}")
                    continue
            
            return all_explores
            
        except Exception as e:
            logging.error(f"Error getting explores: {e}")
            return []
    
    def get_explore_info(self, explore_name: str, model_name: str = None) -> Dict[str, Any]:
        """Get detailed information about a specific explore"""
        try:
            if not hasattr(self, 'sdk') or not self.sdk:
                return {}
            
            # If explore_name contains model prefix, extract it
            if '.' in explore_name and not model_name:
                model_name, explore_name = explore_name.split('.', 1)
            
            # If no model specified, try to find the explore in available models
            if not model_name:
                model_name = self._find_model_for_explore(explore_name)
                if not model_name:
                    return {
                        'name': explore_name,
                        'description': f"Could not find model containing explore '{explore_name}'",
                        'dimensions': [],
                        'measures': [],
                        'error': 'Model not found'
                    }
            
            # Try to get detailed info from database first
            detailed_info = self._get_detailed_explore_info(model_name, explore_name)
            if detailed_info:
                # Cache in memory too
                cache_key = f"{model_name}:{explore_name}"
                self.explores_cache[cache_key] = detailed_info
                return detailed_info
            
            # Fetch detailed info from API
            logging.info(f"Fetching detailed explore info for {model_name}.{explore_name} from Looker API...")
            explore = self.sdk.lookml_model_explore(
                lookml_model_name=model_name,
                explore_name=explore_name
            )
            
            explore_info = {
                'name': explore.name,
                'model': model_name,
                'description': explore.description or f"Data from the {explore_name} explore in {model_name} model",
                'dimensions': [],
                'measures': []
            }
            
            # Get field information
            if hasattr(explore, 'fields') and explore.fields:
                if hasattr(explore.fields, 'dimensions') and explore.fields.dimensions:
                    explore_info['dimensions'] = [
                        {
                            'name': d.name,
                            'label': getattr(d, 'label', d.name),
                            'description': getattr(d, 'description', '')
                        }
                        for d in explore.fields.dimensions[:10]  # Limit to first 10
                        if d.name
                    ]
                
                if hasattr(explore.fields, 'measures') and explore.fields.measures:
                    explore_info['measures'] = [
                        {
                            'name': m.name,
                            'label': getattr(m, 'label', m.name),
                            'description': getattr(m, 'description', '')
                        }
                        for m in explore.fields.measures[:10]  # Limit to first 10
                        if m.name
                    ]
            
            # Save detailed info to database
            self._save_detailed_explore_info(model_name, explore_name, explore_info)
            
            # Cache in memory
            cache_key = f"{model_name}:{explore_name}"
            self.explores_cache[cache_key] = explore_info
            return explore_info
            
        except Exception as e:
            logging.error(f"Error getting explore info for {explore_name} in model {model_name}: {e}")
            return {
                'name': explore_name,
                'model': model_name or 'unknown',
                'description': f"Data from the {explore_name} explore",
                'dimensions': [],
                'measures': [],
                'error': str(e)
            }
    
    def _find_model_for_explore(self, explore_name: str) -> Optional[str]:
        """Find which model contains a specific explore"""
        try:
            models = self.get_available_models()
            for model in models:
                try:
                    model_explores = self.get_available_explores(model['name'])
                    if explore_name in model_explores:
                        return model['name']
                except Exception:
                    continue
            return None
        except Exception as e:
            logging.error(f"Error finding model for explore {explore_name}: {e}")
            return None
    
    def find_relevant_models_and_explores(self, user_question: str) -> Dict[str, Any]:
        """Analyze user question using multiple search strategies with smart fallbacks"""
        try:
            logging.info(f"Analyzing question: '{user_question}'")
            
            # Strategy 1: Try enhanced dashboard context search (works with database)
            try:
                logging.info("Attempting enhanced dashboard context search...")
                enhanced_results = self._comprehensive_similarity_search(user_question)
                
                # Check if we got meaningful results from enhanced search
                if enhanced_results.get('suggested_explores'):
                    # Log what we found for debugging
                    logging.info(f"Enhanced search found {len(enhanced_results['suggested_explores'])} explores: {enhanced_results['suggested_explores']}")
                    
                    # If we found dashboard-enhanced results, prioritize them
                    if enhanced_results.get('dashboard_enhanced', False):
                        logging.info("Dashboard context provided business intelligence - using enhanced results")
                        return enhanced_results
                    
                    # If we found good traditional similarity matches, use them too
                    if enhanced_results.get('total_explores_analyzed', 0) > 0:
                        logging.info("Enhanced similarity analysis provided good matches - using results")
                        return enhanced_results
                    
            except Exception as enhanced_error:
                logging.warning(f"Enhanced search failed (likely database context issue): {enhanced_error}")
            
            # Strategy 2: Try semantic search with field-level analysis
            try:
                logging.info("Attempting semantic field-level search...")
                semantic_results = self._semantic_keyword_search(user_question)
                
                if semantic_results.get('matches', 0) > 0:
                    logging.info(f"Semantic search found {semantic_results['matches']} field-level matches")
                    
                    # If we have AI available, enhance semantic results with AI analysis
                    if hasattr(self, 'llm') and self.llm:
                        logging.info("Enhancing semantic results with AI analysis...")
                        
                        # Get models for context
                        models = self.get_available_models()
                        context = self._build_enhanced_context(user_question, models, semantic_results)
                        
                        # Focused AI prompt for better results
                        prompt = f"""Analyze this user question and match it to the most relevant Looker explores.

User Question: "{user_question}"

{context}

Focus on these key matching criteria:
1. "GX", "ab test", "A/B test", "experiment" → Look for testing/experiment data
2. "cost", "billing", "finance" → Look for financial/cost data  
3. "user", "behavior", "analytics" → Look for user analytics data
4. Exact model/explore name mentions → Prioritize exact matches

Return the TOP 3 most relevant explores with model prefix (e.g., model.explore).

EXPLORES: model.explore1, model.explore2, model.explore3
REASONING: Brief explanation of why these explores match the question"""
                        
                        try:
                            ai_response = self.llm.predict(prompt)
                            
                            # Parse AI response
                            suggested_explores = []
                            reasoning = "AI analysis with semantic field matching"
                            
                            for line in ai_response.strip().split('\\n'):
                                if line.startswith('EXPLORES:'):
                                    explores_text = line.replace('EXPLORES:', '').strip()
                                    suggested_explores = [e.strip() for e in explores_text.split(',') if e.strip()]
                                elif line.startswith('REASONING:'):
                                    reasoning = line.replace('REASONING:', '').strip()
                            
                            if suggested_explores:
                                logging.info(f"AI enhanced semantic search suggests: {suggested_explores}")
                                return {
                                    'suggested_models': models[:3],
                                    'suggested_explores': suggested_explores[:5],
                                    'reasoning': f"{reasoning} (AI + semantic field analysis)",
                                    'semantic_matches': semantic_results.get('matches', 0)
                                }
                        except Exception as ai_error:
                            logging.warning(f"AI enhancement failed: {ai_error}")
                    
                    # Return semantic results without AI enhancement
                    return {
                        'suggested_models': self.get_available_models()[:3],
                        'suggested_explores': semantic_results['relevant_explores'][:5],
                        'reasoning': f"Semantic field-level matching found {semantic_results['matches']} relevant field matches",
                        'semantic_matches': semantic_results.get('matches', 0)
                    }
                    
            except Exception as semantic_error:
                logging.warning(f"Semantic search failed: {semantic_error}")
            
            # Strategy 3: Basic model/explore name similarity matching
            logging.info("Falling back to basic similarity matching...")
            models = self.get_available_models()
            all_explores = []
            
            # Get explores and do basic keyword matching
            query_lower = user_question.lower()
            query_keywords = self._extract_query_keywords(user_question)
            
            scored_explores = []
            
            for model in models[:10]:  # Limit to avoid timeouts
                try:
                    model_explores = self.get_available_explores(model['name'])
                    for explore in model_explores:
                        explore_key = f"{model['name']}.{explore}" if '.' not in explore else explore
                        
                        # Simple keyword matching score
                        score = 0
                        explore_lower = explore_key.lower()
                        
                        # Direct keyword matches
                        for keyword in query_keywords:
                            if keyword in explore_lower:
                                score += 10
                        
                        # Domain-specific boosts
                        if any(term in query_lower for term in ['ab', 'test', 'experiment', 'gx']) and any(term in explore_lower for term in ['test', 'experiment', 'ab']):
                            score += 50
                        
                        if any(term in query_lower for term in ['cost', 'billing', 'finance']) and any(term in explore_lower for term in ['cost', 'billing', 'finance', 'athena']):
                            score += 50
                        
                        if any(term in query_lower for term in ['user', 'behavior']) and any(term in explore_lower for term in ['user', 'behavior']):
                            score += 30
                        
                        if score > 0:
                            scored_explores.append((explore_key, score))
                
                except Exception as explore_error:
                    logging.warning(f"Could not get explores for model {model['name']}: {explore_error}")
                    continue
            
            # Sort by score and return top matches
            scored_explores.sort(key=lambda x: x[1], reverse=True)
            top_explores = [item[0] for item in scored_explores[:5]]
            
            if top_explores:
                logging.info(f"Basic matching found explores: {top_explores}")
                return {
                    'suggested_models': models[:3],
                    'suggested_explores': top_explores,
                    'reasoning': f"Basic keyword matching across available explores (scored {len(scored_explores)} potential matches)",
                    'basic_fallback': True
                }
            
            # Final fallback
            logging.warning("All search strategies failed - returning basic fallback")
            return self._basic_fallback(user_question)
            
        except Exception as e:
            logging.error(f"Complete failure in model/explore suggestion: {e}")
            return self._basic_fallback(user_question)
    
    def _semantic_keyword_search(self, user_question: str) -> Dict[str, Any]:
        """Perform semantic keyword search through cached explore metadata"""
        try:
            from models import LookerExplore
            from app import db
            import re
            
            # Extract keywords from user question
            question_keywords = self._extract_query_keywords(user_question)
            
            if not question_keywords:
                return {'relevant_explores': [], 'matches': 0}
            
            # Search through cached explores
            cutoff_time = datetime.utcnow() - timedelta(hours=self.cache_refresh_hours)
            
            explores = LookerExplore.query.filter(
                LookerExplore.looker_instance_id == self.looker_instance_id,
                LookerExplore.updated_at > cutoff_time
            ).all()
            
            scored_explores = []
            
            for explore in explores:
                score = 0
                matched_fields = []
                
                # Check explore name and description
                if any(keyword in explore.explore_name.lower() for keyword in question_keywords):
                    score += 10
                if explore.description and any(keyword in explore.description.lower() for keyword in question_keywords):
                    score += 5
                
                # Check field metadata
                if explore.explore_metadata and 'field_keywords' in explore.explore_metadata:
                    field_keywords = explore.explore_metadata['field_keywords']
                    for keyword in question_keywords:
                        if keyword in field_keywords:
                            score += 15  # High score for field keyword matches
                
                # Check individual field names and descriptions
                for dimension in explore.dimensions or []:
                    if any(keyword in dimension.get('name', '').lower() for keyword in question_keywords):
                        score += 20  # Very high score for exact field name matches
                        matched_fields.append(f"dimension: {dimension.get('name', '')}")
                    if dimension.get('description') and any(keyword in dimension.get('description', '').lower() for keyword in question_keywords):
                        score += 8
                        matched_fields.append(f"dimension desc: {dimension.get('name', '')}")
                
                for measure in explore.measures or []:
                    if any(keyword in measure.get('name', '').lower() for keyword in question_keywords):
                        score += 20  # Very high score for exact field name matches
                        matched_fields.append(f"measure: {measure.get('name', '')}")
                    if measure.get('description') and any(keyword in measure.get('description', '').lower() for keyword in question_keywords):
                        score += 8
                        matched_fields.append(f"measure desc: {measure.get('name', '')}")
                
                if score > 0:
                    scored_explores.append({
                        'explore': f"{explore.model_name}.{explore.explore_name}",
                        'score': score,
                        'matched_fields': matched_fields[:3]  # Top 3 matches
                    })
            
            # Sort by score and return top matches
            scored_explores.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'relevant_explores': [item['explore'] for item in scored_explores[:10]],
                'matches': len(scored_explores),
                'top_matches': scored_explores[:5]
            }
            
        except Exception as e:
            logging.error(f"Error in semantic keyword search: {e}")
            return {'relevant_explores': [], 'matches': 0}
    
    def _extract_query_keywords(self, user_question: str) -> List[str]:
        """Extract relevant keywords from user question for semantic search"""
        import re
        
        # Convert to lowercase
        question = user_question.lower()
        
        # Extract meaningful words (length > 2, not common stop words)
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'how', 'what', 'when', 'where', 'who', 'why', 'which', 'that', 'this', 'these', 'those', 'we', 'our', 'us', 'i', 'my', 'me', 'you', 'your', 'many'}
        
        words = re.findall(r'\b\w+\b', question)
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Add some domain-specific term expansions
        expanded_keywords = keywords.copy()
        for keyword in keywords:
            if keyword in ['ab', 'a/b']:
                expanded_keywords.extend(['test', 'experiment', 'variant'])
            elif keyword in ['test', 'testing']:
                expanded_keywords.extend(['experiment', 'variant', 'winner', 'ab'])
            elif keyword in ['winner', 'winners']:
                expanded_keywords.extend(['success', 'conversion', 'result'])
        
        return list(set(expanded_keywords))
    
    def _build_enhanced_context(self, user_question: str, models: List[Dict], semantic_results: Dict) -> str:
        """Build enhanced context with model and explore metadata for AI"""
        context_parts = []
        
        # Add models with descriptions
        if models:
            context_parts.append("Available Models:")
            for model in models[:8]:  # Limit to avoid context overflow
                context_parts.append(f"- {model['name']}: {model.get('description', 'No description')}")
        
        # Add top semantic matches with detailed field information
        if semantic_results.get('top_matches'):
            context_parts.append("\nMost Relevant Explores (based on field analysis):")
            
            for match in semantic_results['top_matches'][:5]:
                explore_name = match['explore']
                score = match['score']
                matched_fields = match['matched_fields']
                
                context_parts.append(f"- {explore_name} (relevance: {score})")
                if matched_fields:
                    context_parts.append(f"  Matching fields: {', '.join(matched_fields)}")
        
        # Add other explores for completeness (but less detail)
        all_explores = self.get_available_explores()
        other_explores = [e for e in all_explores if e not in [m['explore'] for m in semantic_results.get('top_matches', [])]]
        if other_explores:
            context_parts.append(f"\nOther Available Explores: {', '.join(other_explores[:10])}")
        
        return "\n".join(context_parts)
    
    def _comprehensive_similarity_search(self, user_question: str) -> Dict[str, Any]:
        """Perform comprehensive similarity search with dashboard context and description prioritization"""
        try:
            logging.info("Starting enhanced similarity search with dashboard context and description prioritization...")
            
            # Extract keywords from user question
            query_keywords = self._extract_query_keywords(user_question)
            
            # Get all available models, explores, and dashboards
            all_models = self.get_available_models()
            all_dashboards = self.get_available_dashboards()
            
            # Score models with enhanced description weighting
            scored_models = []
            for model in all_models:
                score = self._calculate_enhanced_similarity_score(
                    user_question, 
                    model['name'], 
                    model.get('description', ''), 
                    query_keywords,
                    description_weight=5.0  # Weight descriptions 5x higher than names
                )
                if score > 0:
                    scored_models.append({
                        'model': model,
                        'score': score,
                        'match_reason': f"Enhanced model similarity with description prioritization"
                    })
            
            scored_models.sort(key=lambda x: x['score'], reverse=True)
            
            # Score dashboards for business context (NEW)
            scored_dashboards = []
            for dashboard in all_dashboards:
                dashboard_score = self._calculate_enhanced_similarity_score(
                    user_question,
                    dashboard.get('title', ''),
                    dashboard.get('description', ''),
                    query_keywords,
                    description_weight=8.0  # Weight dashboard descriptions even higher
                )
                
                if dashboard_score > 0:
                    scored_dashboards.append({
                        'dashboard': dashboard,
                        'score': dashboard_score,
                        'explore_refs': dashboard.get('explore_references', [])
                    })
            
            scored_dashboards.sort(key=lambda x: x['score'], reverse=True)
            
            # Use dashboard context to find relevant explores (KEY ENHANCEMENT)
            dashboard_suggested_explores = []
            for scored_dash in scored_dashboards[:3]:  # Top 3 dashboards
                explore_refs = scored_dash.get('explore_refs', [])
                for explore_ref in explore_refs:
                    if explore_ref not in dashboard_suggested_explores:
                        dashboard_suggested_explores.append({
                            'explore': explore_ref,
                            'dashboard_context': scored_dash['dashboard'].get('title', ''),
                            'business_score': scored_dash['score']
                        })
            
            # Score traditional explores with enhanced field matching
            top_models = [item['model']['name'] for item in scored_models[:5]]
            scored_explores = []
            
            for model_name in top_models:
                try:
                    model_explores = self.get_available_explores(model_name)
                    
                    for explore in model_explores:
                        # Get detailed explore info for description matching
                        try:
                            explore_info = self.get_explore_info(explore, model_name)
                            explore_description = explore_info.get('description', '')
                            
                            # Calculate enhanced similarity with description priority
                            explore_score = self._calculate_enhanced_similarity_score(
                                user_question,
                                explore,
                                explore_description,
                                query_keywords,
                                description_weight=5.0
                            )
                            
                            # Boost score for field-level matches
                            if explore_info and 'dimensions' in explore_info:
                                for dim in explore_info.get('dimensions', [])[:10]:
                                    field_name = dim.get('name', '').lower()
                                    field_desc = dim.get('description', '').lower()
                                    
                                    # Field name matches get high score
                                    if any(keyword in field_name for keyword in query_keywords):
                                        explore_score += 30
                                    
                                    # Field description matches get very high score (NEW)
                                    if field_desc and any(keyword in field_desc for keyword in query_keywords):
                                        explore_score += 50  # Higher than field names
                                
                                for measure in explore_info.get('measures', [])[:10]:
                                    field_name = measure.get('name', '').lower()
                                    field_desc = measure.get('description', '').lower()
                                    
                                    if any(keyword in field_name for keyword in query_keywords):
                                        explore_score += 30
                                    
                                    if field_desc and any(keyword in field_desc for keyword in query_keywords):
                                        explore_score += 50
                            
                            if explore_score > 0:
                                scored_explores.append({
                                    'explore': f"{model_name}.{explore}" if '.' not in explore else explore,
                                    'score': explore_score,
                                    'model_name': model_name,
                                    'source': 'traditional_search'
                                })
                        
                        except Exception as detail_error:
                            # Fallback to basic scoring if detailed info fails
                            basic_score = self._calculate_enhanced_similarity_score(
                                user_question, explore, '', query_keywords
                            )
                            if basic_score > 0:
                                scored_explores.append({
                                    'explore': f"{model_name}.{explore}" if '.' not in explore else explore,
                                    'score': basic_score,
                                    'model_name': model_name,
                                    'source': 'basic_search'
                                })
                
                except Exception as e:
                    logging.warning(f"Could not get explores for model {model_name}: {e}")
                    continue
            
            # Merge dashboard-suggested explores with traditional explores
            final_scored_explores = []
            
            # Add dashboard-suggested explores with boosted scores (BUSINESS CONTEXT BOOST)
            for dash_explore in dashboard_suggested_explores:
                final_scored_explores.append({
                    'explore': dash_explore['explore'],
                    'score': dash_explore['business_score'] + 100,  # Big boost for dashboard context
                    'source': 'dashboard_context',
                    'dashboard_context': dash_explore['dashboard_context']
                })
            
            # Add traditional scored explores
            final_scored_explores.extend(scored_explores)
            
            # Sort all explores by score
            final_scored_explores.sort(key=lambda x: x['score'], reverse=True)
            
            # Remove duplicates while preserving order
            seen_explores = set()
            unique_explores = []
            for item in final_scored_explores:
                if item['explore'] not in seen_explores:
                    seen_explores.add(item['explore'])
                    unique_explores.append(item)
            
            # Prepare results
            top_models_result = [item['model'] for item in scored_models[:3]]
            top_explores_result = [item['explore'] for item in unique_explores[:5]]
            
            # Enhanced reasoning with dashboard context
            reasoning = f"Enhanced similarity search with dashboard context: analyzed {len(all_models)} models, {len(all_dashboards)} dashboards. "
            
            if unique_explores:
                top_result = unique_explores[0]
                reasoning += f"Top match: {top_result['explore']} (score: {top_result['score']:.1f})"
                
                if top_result.get('source') == 'dashboard_context':
                    reasoning += f" - found via business dashboard context: '{top_result.get('dashboard_context', '')}'."
                elif top_result['score'] >= 50:
                    reasoning += " - matched field descriptions with high relevance."
                elif top_result['score'] >= 30:
                    reasoning += " - matched field names in explore metadata."
                else:
                    reasoning += " - matched through enhanced description similarity."
            else:
                reasoning += "No strong matches found in enhanced analysis."
            
            return {
                'suggested_models': top_models_result,
                'suggested_explores': top_explores_result,
                'reasoning': reasoning,
                'similarity_search': True,
                'dashboard_enhanced': True,
                'dashboard_matches': len(dashboard_suggested_explores),
                'total_explores_analyzed': len(unique_explores)
            }
            
        except Exception as e:
            logging.error(f"Error in enhanced similarity search: {e}")
            return self._basic_fallback(user_question)
    
    def _calculate_similarity_score(self, user_question: str, target_name: str, target_description: str, query_keywords: List[str]) -> int:
        """Calculate similarity score between user question and target name/description"""
        score = 0
        target_lower = target_name.lower()
        desc_lower = target_description.lower() if target_description else ""
        question_lower = user_question.lower()
        
        # Direct substring matches in name (high score)
        for keyword in query_keywords:
            if keyword in target_lower:
                score += 25
        
        # Fuzzy string matching using simple character overlap
        common_chars = set(question_lower) & set(target_lower)
        if len(common_chars) >= 3:
            score += len(common_chars)
        
        # Description matches (lower score)
        if desc_lower:
            for keyword in query_keywords:
                if keyword in desc_lower:
                    score += 10
        
        # Boost for exact word matches
        target_words = set(target_name.lower().replace('_', ' ').split())
        question_words = set(question_lower.split())
        word_matches = len(target_words & question_words)
        score += word_matches * 15
        
        return score
    
    def _calculate_enhanced_similarity_score(self, user_question: str, target_name: str, target_description: str, query_keywords: List[str], description_weight: float = 5.0) -> float:
        """Calculate enhanced similarity score with heavy weighting on descriptions over names"""
        score = 0.0
        target_lower = target_name.lower()
        desc_lower = target_description.lower() if target_description else ""
        question_lower = user_question.lower()
        
        # === NAME-BASED SCORING (Base weight) ===
        name_score = 0
        
        # Direct keyword matches in name
        for keyword in query_keywords:
            if keyword in target_lower:
                name_score += 10  # Reduced from 25 to make room for description weighting
        
        # Exact word matches in name
        target_words = set(target_name.lower().replace('_', ' ').split())
        question_words = set(question_lower.split())
        word_matches = len(target_words & question_words)
        name_score += word_matches * 8  # Reduced from 15
        
        # Character overlap for fuzzy matching
        common_chars = set(question_lower) & set(target_lower)
        if len(common_chars) >= 3:
            name_score += len(common_chars) * 0.5
        
        # === DESCRIPTION-BASED SCORING (Heavily weighted) ===
        description_score = 0
        
        if desc_lower and desc_lower.strip():
            # Direct keyword matches in description (MUCH higher weight)
            for keyword in query_keywords:
                if keyword in desc_lower:
                    description_score += 25  # High base score for description matches
            
            # Multi-word phrase matching in descriptions
            question_phrases = []
            words = question_lower.split()
            # Create 2-word and 3-word phrases
            for i in range(len(words) - 1):
                question_phrases.append(' '.join(words[i:i+2]))
                if i < len(words) - 2:
                    question_phrases.append(' '.join(words[i:i+3]))
            
            for phrase in question_phrases:
                if len(phrase.strip()) > 5 and phrase in desc_lower:
                    description_score += 40  # Very high score for phrase matches
            
            # Word overlap in descriptions (semantic matching)
            desc_words = set(desc_lower.replace('_', ' ').split())
            desc_word_matches = len(desc_words & question_words)
            description_score += desc_word_matches * 15
            
            # Boost for business terminology in descriptions
            business_terms = ['analysis', 'report', 'dashboard', 'kpi', 'metric', 'performance', 
                             'overview', 'summary', 'insights', 'trends', 'data', 'analytics']
            business_matches = sum(1 for term in business_terms if term in desc_lower)
            if business_matches > 0 and any(term in question_lower for term in business_terms):
                description_score += business_matches * 10
        
        # === DOMAIN-SPECIFIC ENHANCEMENTS ===
        domain_boost = 0
        
        # A/B testing and experiments boost
        ab_test_terms = ['ab', 'a/b', 'test', 'experiment', 'variant', 'winner', 'gx']
        ab_test_in_question = sum(1 for term in ab_test_terms if term in question_lower)
        ab_test_in_target = sum(1 for term in ab_test_terms if term in target_lower or term in desc_lower)
        
        if ab_test_in_question > 0 and ab_test_in_target > 0:
            domain_boost += ab_test_in_question * ab_test_in_target * 20
        
        # User behavior and analytics boost  
        user_terms = ['user', 'behavior', 'session', 'signup', 'conversion']
        user_in_question = sum(1 for term in user_terms if term in question_lower)
        user_in_target = sum(1 for term in user_terms if term in target_lower or term in desc_lower)
        
        if user_in_question > 0 and user_in_target > 0:
            domain_boost += user_in_question * user_in_target * 15
        
        # === FINAL SCORE CALCULATION ===
        # Apply description weighting (5x or higher)
        weighted_description_score = description_score * description_weight
        
        # Combine all components
        total_score = name_score + weighted_description_score + domain_boost
        
        # Bonus for having both name and description matches
        if name_score > 0 and description_score > 0:
            total_score *= 1.2  # 20% bonus for comprehensive matches
        
        return total_score
    
    def _comprehensive_search_fallback(self, user_question: str) -> Dict[str, Any]:
        """Comprehensive fallback with robust error handling"""
        try:
            # Try semantic search first if database is available
            semantic_results = self._semantic_keyword_search(user_question)
            
            if semantic_results.get('matches', 0) > 0:
                models = self.get_available_models()
                return {
                    'suggested_models': models[:3],
                    'suggested_explores': semantic_results['relevant_explores'][:5],
                    'reasoning': f"Semantic keyword matching found {semantic_results['matches']} field-level matches",
                    'semantic_matches': semantic_results.get('matches', 0)
                }
            else:
                # Try enhanced similarity search  
                try:
                    return self._comprehensive_similarity_search(user_question)
                except Exception:
                    # If enhanced search fails, do basic matching
                    logging.warning("Enhanced similarity search failed, using basic fallback")
                    return self._basic_fallback(user_question)
                
        except Exception as e:
            logging.error(f"Error in comprehensive search fallback: {e}")
            return self._basic_fallback(user_question)
    
    def _basic_fallback(self, user_question: str) -> Dict[str, Any]:
        """Basic fallback when all other methods fail"""
        models = self.get_available_models()
        explores = self.get_available_explores()
        
        return {
            'suggested_models': models[:3] if models else [],
            'suggested_explores': explores[:5] if explores else [],
            'reasoning': "All advanced matching failed. Showing basic model/explore list. Please try more specific keywords or check if the models you're looking for exist.",
            'fallback': True
        }
    
    def run_looker_query(self, query_request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Looker query and return results"""
        try:
            if not hasattr(self, 'sdk') or not self.sdk:
                return {'error': 'Looker SDK not initialized'}
            
            # Run the query
            query = self.sdk.create_query(query_request)
            result = self.sdk.run_query(query.id, result_format='json')
            
            return {
                'success': True,
                'data': result,
                'query_id': query.id
            }
            
        except Exception as e:
            logging.error(f"Error running Looker query: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_response(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Get a response from the Looker agent for the user's analytical question
        
        Args:
            user_message: The user's question or request
            chat_history: Previous chat exchanges for context
            
        Returns:
            String response from the agent
        """
        # Check if credentials are available
        if not self.credentials_available:
            return self._get_credentials_error_message()
        
        try:
            # Prepare context from chat history
            context = ""
            if chat_history:
                # Include last few exchanges for context
                recent_history = chat_history[-3:] if len(chat_history) > 3 else chat_history
                for exchange in recent_history:
                    context += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
            
            # Combine context with current message
            full_message = f"{context}User: {user_message}" if context else user_message
            
            user_message_lower = user_message.lower().strip()
            
            # Handle dashboard-specific queries (NEW - highest priority)
            if any(keyword in user_message_lower for keyword in ['dashboard', 'dashboards']) and \
               any(keyword in user_message_lower for keyword in ['for', 'about', 'show', 'find', 'there']):
                return self._handle_dashboard_query(user_message)
            
            # Handle specific explore information requests first (more specific)
            if any(keyword in user_message_lower for keyword in ['dimensions', 'measures', 'fields']) or \
               ('explore' in user_message_lower and any(keyword in user_message_lower for keyword in ['info', 'about', 'describe'])):
                return self._handle_explore_info_request(user_message)
            
            # Handle explores/tables listing requests
            if any(keyword in user_message_lower for keyword in ['explores', 'tables', 'available', 'list', 'show me']):
                if any(keyword in user_message_lower for keyword in ['explore', 'table']):
                    return self._handle_explores_request(user_message)
            
            # Handle model listing requests and specific model existence queries
            if any(keyword in user_message_lower for keyword in ['models', 'model']):
                if any(keyword in user_message_lower for keyword in ['available', 'list', 'show', 'what']):
                    return self._handle_models_request()
                elif any(keyword in user_message_lower for keyword in ['called', 'named', 'there a model']):
                    return self._handle_specific_model_query(user_message)
            
            # Handle simple count queries
            if any(keyword in user_message_lower for keyword in ['how many', 'count', 'total', 'number of']):
                return self._handle_count_query(user_message, chat_history)
            
            # For other analytical questions, use OpenAI to understand intent and generate a response
            return self._handle_analytical_query(user_message, chat_history)
            
        except Exception as e:
            logging.error(f"Error getting response from Looker agent: {e}")
            error_msg = "I encountered an issue while processing your request. "
            
            if "authentication" in str(e).lower():
                error_msg += "There seems to be an authentication problem with Looker. Please check the connection settings."
            elif "timeout" in str(e).lower():
                error_msg += "The query took too long to process. Please try a more specific question or try again later."
            elif "not found" in str(e).lower():
                error_msg += "I couldn't find the requested data or dashboard. Please verify the data source exists."
            else:
                error_msg += "Please try rephrasing your question or contact support if the issue persists."
            
            return error_msg
    
    def _handle_models_request(self) -> str:
        """Handle requests for listing available models"""
        try:
            models = self.get_available_models()
            if not models:
                return "No LookML models are currently accessible. Please check with your Looker administrator about model permissions."
            
            response = f"📦 Available LookML models:\n\n"
            
            # Group models for better presentation
            for i, model in enumerate(models[:10], 1):  # Limit to first 10
                response += f"{i:2d}. **{model['name']}**"
                if model.get('description'):
                    response += f" - {model['description'][:80]}{'...' if len(model['description']) > 80 else ''}"
                if model.get('project_name'):
                    response += f" _(Project: {model['project_name']})_"
                response += "\n"
            
            if len(models) > 10:
                response += f"\n... and {len(models) - 10} more models\n"
            
            response += f"\n📈 Total: {len(models)} models available"
            response += "\n\n💡 Ask me about explores in a specific model or request data analysis!"
            
            return response
            
        except Exception as e:
            logging.error(f"Error handling models request: {e}")
            return "I couldn't retrieve the list of available models. Please try again later."
    
    def _handle_dashboard_query(self, user_message: str) -> str:
        """Handle queries specifically asking about dashboards (e.g., 'is there a dashboard for X?')"""
        try:
            logging.info(f"Handling dashboard-specific query: '{user_message}'")
            
            # Get all available dashboards
            dashboards = self.get_available_dashboards()
            
            if not dashboards:
                return "I couldn't retrieve any dashboards at the moment. This might be due to permissions or connectivity issues. Please check with your Looker administrator."
            
            # Extract query keywords for matching
            query_keywords = self._extract_query_keywords(user_message)
            
            # Score dashboards using enhanced similarity with high description weighting
            scored_dashboards = []
            
            for dashboard in dashboards:
                score = self._calculate_enhanced_similarity_score(
                    user_message,
                    dashboard.get('title', ''),
                    dashboard.get('description', ''),
                    query_keywords,
                    description_weight=10.0  # Very high weight for dashboard descriptions
                )
                
                if score > 0:
                    dashboard_info = {
                        'dashboard': dashboard,
                        'score': score,
                        'title': dashboard.get('title', ''),
                        'description': dashboard.get('description', ''),
                        'folder': dashboard.get('folder', ''),
                        'explore_refs': dashboard.get('explore_references', [])
                    }
                    scored_dashboards.append(dashboard_info)
            
            # Sort by score and get top matches
            scored_dashboards.sort(key=lambda x: x['score'], reverse=True)
            top_dashboards = scored_dashboards[:5]
            
            if not top_dashboards:
                return f"I couldn't find any dashboards that match '{user_message}'. You might want to try different keywords or check if the dashboard you're looking for exists in your Looker instance."
            
            # Build response with dashboard information
            response = "📊 I found these relevant dashboards for your query:\n\n"
            
            for i, dash_info in enumerate(top_dashboards, 1):
                dashboard = dash_info['dashboard']
                title = dash_info['title'] or f"Dashboard {dashboard.get('id', 'Unknown')}"
                description = dash_info['description'] or "No description available"
                folder = dash_info['folder']
                
                # Generate dashboard URL
                dashboard_url = self._generate_dashboard_url(dashboard.get('id', ''))
                
                response += f"**{i}. {title}**"
                if folder:
                    response += f" _(in {folder})_"
                response += "\n"
                
                # Add description
                if description and len(description) > 10:
                    response += f"   📝 {description[:120]}{'...' if len(description) > 120 else ''}\n"
                
                # Add URL
                if dashboard_url:
                    response += f"   🔗 **[Open Dashboard]({dashboard_url})**\n"
                
                # Add related explores for additional context
                explore_refs = dash_info['explore_refs']
                if explore_refs:
                    response += f"   📊 Data from: {', '.join(explore_refs[:3])}"
                    if len(explore_refs) > 3:
                        response += f" (and {len(explore_refs) - 3} more)"
                    response += "\n"
                
                response += "\n"
            
            # Add summary and suggestions
            response += f"🎯 **Found {len(top_dashboards)} relevant dashboard{'s' if len(top_dashboards) != 1 else ''}** based on your query.\n\n"
            
            # Also suggest related explores for deeper analysis
            all_explore_refs = set()
            for dash_info in top_dashboards[:3]:  # Top 3 dashboards
                all_explore_refs.update(dash_info['explore_refs'])
            
            if all_explore_refs:
                response += f"💡 **For deeper analysis**, you can also explore the data directly using:\n"
                response += f"📈 **Explores**: {', '.join(list(all_explore_refs)[:5])}\n"
                if len(all_explore_refs) > 5:
                    response += f"   (and {len(all_explore_refs) - 5} more related explores)\n"
            
            return response
            
        except Exception as e:
            logging.error(f"Error handling dashboard query: {e}")
            return "I encountered an error while searching for dashboards. Please try rephrasing your question or check if you have access to dashboards in your Looker instance."
    
    def _generate_dashboard_url(self, dashboard_id: str) -> str:
        """Generate a complete URL for a Looker dashboard"""
        try:
            if not dashboard_id or not self.looker_base_url:
                return ""
            
            # Remove trailing slash from base URL if present
            base_url = self.looker_base_url.rstrip('/')
            
            # Construct dashboard URL
            dashboard_url = f"{base_url}/dashboards/{dashboard_id}"
            
            return dashboard_url
            
        except Exception as e:
            logging.warning(f"Error generating dashboard URL for {dashboard_id}: {e}")
            return ""
    
    def _handle_specific_model_query(self, user_message: str) -> str:
        """Handle queries asking about specific model existence (e.g., 'is there a model called X?')"""
        try:
            import re
            
            # Extract potential model name from the query
            patterns = [
                r'model\s+called\s+([\w_]+)',
                r'model\s+named\s+([\w_]+)', 
                r'there\s+a\s+model\s+([\w_]+)',
                r'model\s+([\w_]+)'
            ]
            
            potential_model_name = None
            for pattern in patterns:
                match = re.search(pattern, user_message.lower())
                if match:
                    potential_model_name = match.group(1)
                    break
            
            if not potential_model_name:
                return "I couldn't identify the specific model name you're asking about. Please try asking like 'Is there a model called model_name?'"
            
            # Check if model exists exactly
            models = self.get_available_models()
            exact_match = None
            
            for model in models:
                if model['name'].lower() == potential_model_name.lower():
                    exact_match = model
                    break
            
            if exact_match:
                response = f"✅ Yes, there is a model called **{exact_match['name']}**"
                if exact_match.get('description'):
                    response += f"\n\n📝 Description: {exact_match['description']}"
                if exact_match.get('project_name'):
                    response += f"\n🗂️ Project: {exact_match['project_name']}"
                
                # Get explores for this model
                try:
                    explores = self.get_available_explores(exact_match['name'])
                    if explores:
                        response += f"\n\n📊 This model has {len(explores)} explore(s): {', '.join(explores[:5])}"
                        if len(explores) > 5:
                            response += f" (and {len(explores) - 5} more)"
                except:
                    pass
                
                return response
            else:
                # Model doesn't exist exactly - try similarity search
                logging.info(f"Exact model '{potential_model_name}' not found, trying similarity search...")
                
                # Use comprehensive similarity search
                similarity_results = self._comprehensive_similarity_search(f"model {potential_model_name}")
                
                response = f"❌ No model named exactly **'{potential_model_name}'** was found."
                
                if similarity_results.get('suggested_models'):
                    response += "\n\n🔍 However, I found some similar models that might be what you're looking for:"
                    for model in similarity_results['suggested_models'][:3]:
                        response += f"\n• **{model['name']}**"
                        if model.get('description'):
                            response += f" - {model['description'][:60]}{'...' if len(model['description']) > 60 else ''}"
                
                response += "\n\n💡 Try asking about one of these models, or use 'What models are available?' to see the full list."
                
                return response
                
        except Exception as e:
            logging.error(f"Error handling specific model query: {e}")
            return f"I encountered an error while searching for the model. Please try asking 'What models are available?' to see the full list."
    
    def _handle_explores_request(self, user_message: str) -> str:
        """Handle requests for listing available explores"""
        try:
            # Check if user is asking for explores in a specific model
            models = self.get_available_models()
            specific_model = None
            
            for model in models:
                if model['name'].lower() in user_message.lower():
                    specific_model = model['name']
                    break
            
            if specific_model:
                explores = self.get_available_explores(specific_model)
                if not explores:
                    return f"No explores are currently accessible in the '{specific_model}' model. Please check with your Looker administrator about model permissions."
                
                response = f"📊 Available explores in the '{specific_model}' model:\n\n"
                
                # Group explores for better presentation
                for i, explore in enumerate(explores[:15], 1):  # Limit to first 15
                    response += f"{i:2d}. **{explore}**\n"
                
                if len(explores) > 15:
                    response += f"\n... and {len(explores) - 15} more explores\n"
                
                response += f"\n📈 Total: {len(explores)} explores available in {specific_model}"
                response += "\n\n💡 Ask me about a specific explore or request data analysis!"
                
                return response
            else:
                # Show explores from all models
                all_explores = self.get_available_explores()
                if not all_explores:
                    return "No explores are currently accessible. Please check with your Looker administrator about model permissions."
                
                response = f"📊 Available explores across all models:\n\n"
                
                # Group explores by model for better presentation
                model_groups = {}
                for explore in all_explores:
                    if '.' in explore:
                        model_name, explore_name = explore.split('.', 1)
                        if model_name not in model_groups:
                            model_groups[model_name] = []
                        model_groups[model_name].append(explore_name)
                
                for model_name, explores in list(model_groups.items())[:5]:  # Show first 5 models
                    response += f"**{model_name}**: {', '.join(explores[:5])}"
                    if len(explores) > 5:
                        response += f" (and {len(explores) - 5} more)"
                    response += "\n"
                
                if len(model_groups) > 5:
                    response += f"\n... and {len(model_groups) - 5} more models\n"
                
                response += f"\n📈 Total: {len(all_explores)} explores available"
                response += "\n\n💡 Ask me about explores in a specific model or request data analysis!"
                
                return response
            
        except Exception as e:
            logging.error(f"Error handling explores request: {e}")
            return "I couldn't retrieve the list of available explores. Please try again later."
    
    def _handle_explore_info_request(self, user_message: str) -> str:
        """Handle requests for information about a specific explore"""
        try:
            # Extract explore name from the message (improved approach)
            all_explores = self.get_available_explores()
            mentioned_explore = None
            mentioned_model = None
            
            # First, try exact matches and quoted strings
            import re
            quoted_match = re.search(r'"([^"]+)"', user_message)
            if quoted_match:
                quoted_explore = quoted_match.group(1)
                for explore in all_explores:
                    if '.' in explore:
                        model_name, explore_name = explore.split('.', 1)
                        if explore_name.lower() == quoted_explore.lower():
                            mentioned_explore = explore_name
                            mentioned_model = model_name
                            break
                    elif explore.lower() == quoted_explore.lower():
                        mentioned_explore = explore
                        break
            
            # If no quoted match, look for explore names in the message
            if not mentioned_explore:
                for explore in all_explores:
                    if '.' in explore:
                        model_name, explore_name = explore.split('.', 1)
                        if explore_name.lower() in user_message.lower():
                            mentioned_explore = explore_name
                            mentioned_model = model_name
                            break
                    elif explore.lower() in user_message.lower():
                        mentioned_explore = explore
                        break
            
            if not mentioned_explore:
                # Show available explores grouped by model
                sample_explores = []
                for explore in all_explores[:5]:
                    if '.' in explore:
                        sample_explores.append(explore.split('.', 1)[1])  # Remove model prefix for display
                    else:
                        sample_explores.append(explore)
                return f"Please specify which explore you'd like to know more about. Available explores: {', '.join(sample_explores)}{'...' if len(all_explores) > 5 else ''}"
            
            explore_info = self.get_explore_info(mentioned_explore, mentioned_model)
            
            model_display = f" (in {explore_info.get('model', 'unknown')} model)" if explore_info.get('model') else ""
            response = f"📊 **{explore_info['name']}** explore{model_display}:\n\n"
            response += f"📝 {explore_info['description']}\n\n"
            
            if explore_info['dimensions']:
                response += "📏 **Sample Dimensions:**\n"
                for dim in explore_info['dimensions'][:5]:
                    response += f"   • {dim['label'] or dim['name']}"
                    if dim['description']:
                        response += f": {dim['description'][:50]}{'...' if len(dim['description']) > 50 else ''}"
                    response += "\n"
                response += "\n"
            
            if explore_info['measures']:
                response += "📈 **Sample Measures:**\n"
                for measure in explore_info['measures'][:5]:
                    response += f"   • {measure['label'] or measure['name']}"
                    if measure['description']:
                        response += f": {measure['description'][:50]}{'...' if len(measure['description']) > 50 else ''}"
                    response += "\n"
                response += "\n"
            
            response += "💡 Ask me to analyze data from this explore!"
            
            return response
            
        except Exception as e:
            logging.error(f"Error handling explore info request: {e}")
            return "I couldn't retrieve information about that explore. Please try again."
    
    def _handle_analytical_query(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Handle analytical queries using OpenAI to understand intent"""
        try:
            # Use AI to find relevant models and explores for the query
            suggestions = self.find_relevant_models_and_explores(user_message)
            
            # Get basic explore information
            all_explores = self.get_available_explores()
            
            if not all_explores:
                return "I don't have access to any data explores at the moment. Please check with your Looker administrator."
            
            # Use OpenAI to provide a more intelligent response
            context = ""
            if chat_history:
                recent_history = chat_history[-2:] if len(chat_history) > 2 else chat_history
                for exchange in recent_history:
                    context += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
            
            context_section = f"Recent conversation context:\n{context}" if context else ""
            
            # Include AI suggestions in the response
            suggested_models_text = ", ".join([m['name'] for m in suggestions['suggested_models']])
            suggested_explores_text = ", ".join(suggestions['suggested_explores'][:3])  # Top 3
            
            prompt = f"""You are a Looker BI assistant. The user is asking: "{user_message}"

Based on AI analysis, the most relevant models are: {suggested_models_text}
Most relevant explores are: {suggested_explores_text}
Reasoning: {suggestions['reasoning']}

{context_section}

Provide a helpful response about what data analysis is possible with these relevant models and explores. 
If the user is asking for specific data, explain that you can help them understand what's available but they would need to run queries through Looker's interface.
Be conversational and helpful, focusing on the AI-suggested relevant explores.
Keep the response under 200 words."""

            response = self.llm.predict(prompt)
            
            # Add the AI suggestions
            if suggestions['suggested_models']:
                response += f"\n\n🎯 **Recommended models**: {suggested_models_text}"
            if suggestions['suggested_explores']:
                response += f"\n📊 **Suggested explores**: {suggested_explores_text}"
            response += "\n💡 Ask me about specific explores or 'What models are available?' to see all options!"
            
            return response.strip()
            
        except Exception as e:
            logging.error(f"Error handling analytical query: {e}")
            return "I can help you understand what data is available in your Looker instance. Try asking 'What explores are available?' to get started!"
    
    def _handle_count_query(self, user_message: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """Handle count/total queries by running simple Looker queries"""
        try:
            user_message_lower = user_message.lower()
            
            # Try to identify what the user wants to count
            if 'user' in user_message_lower:
                # Try to run a query for unique users
                try:
                    # Get the session explore to see what measures are available
                    session_info = self.get_explore_info('session')
                    
                    if session_info and session_info.get('measures') and len(session_info['measures']) > 0:
                        # Use the first available measure from session
                        first_measure = session_info['measures'][0]['name']
                        session_model = session_info.get('model', 'unknown')
                        
                        query_request = {
                            'model': session_model,
                            'explore': 'session',
                            'fields': [first_measure],
                            'limit': '1'
                        }
                        
                        result = self.run_looker_query(query_request)
                        
                        if result.get('success') and result.get('data'):
                            import json
                            data = json.loads(result['data']) if isinstance(result['data'], str) else result['data']
                            if data and len(data) > 0:
                                count = list(data[0].values())[0] if data[0] else "unknown"
                                return f"Based on the session data, I found approximately **{count}** sessions. Note that this represents sessions, which may be a good proxy for website visitors, though the exact count of unique users would require a more specific query in Looker."
                    
                    # If we get here, the query didn't work as expected
                    return f"I can help you find user data in the **session** explore, which contains information about website sessions and user interactions. Based on the available data, you have these measures: {', '.join([m['label'] for m in session_info.get('measures', [])[:3]])}. To get exact user counts, you'd need to run a query in Looker."
                    
                except Exception as query_error:
                    logging.error(f"Query execution failed: {query_error}")
                    return f"I can help you find user data in the **session** explore, which contains information about website sessions and user interactions. To get exact user counts, you'd need to run a query in Looker using dimensions like user IDs and measures like session counts."
            
            # Use AI to find relevant explores for count queries
            suggestions = self.find_relevant_models_and_explores(user_message)
            relevant_explores = suggestions['suggested_explores'][:3]
            
            if relevant_explores:
                return f"For that count query, you should look at these explores: **{', '.join(relevant_explores)}**. These contain the data you need to answer your question. You can run queries in Looker to get exact counts."
            else:
                return f"I'd suggest exploring the available data based on your specific count needs. Ask me 'What explores are available?' to see all options or be more specific about what you want to count."
            
        except Exception as e:
            logging.error(f"Error handling count query: {e}")
            return "I can help you understand which explores contain count data. Try asking about specific explores or 'What explores are available?' to get started."
    
    def _get_credentials_error_message(self) -> str:
        """Return an informative message about missing credentials"""
        missing_vars = []
        if not self.looker_base_url:
            missing_vars.append('LOOKER_BASE_URL')
        if not self.looker_client_id:
            missing_vars.append('LOOKER_CLIENT_ID')
        if not self.looker_client_secret:
            missing_vars.append('LOOKER_CLIENT_SECRET')
        if not self.openai_api_key:
            missing_vars.append('OPENAI_API_KEY')
        # LOOKML_MODEL_NAME is no longer required
        
        return f"""I'm unable to connect to your Looker BI platform because some required configuration is missing.

To enable data analysis, I need the following environment variables to be set:
• LOOKER_BASE_URL - Your Looker instance URL
• LOOKER_CLIENT_ID - Your Looker API client ID
• LOOKER_CLIENT_SECRET - Your Looker API client secret
• OPENAI_API_KEY - OpenAI API key for natural language processing

Missing: {', '.join(missing_vars)}

Note: LOOKML_MODEL_NAME is no longer required - I can now discover and work with all available models automatically!

Please configure these credentials to start analyzing your data!"""
    
    def test_connection(self) -> bool:
        """
        Test the connection to Looker
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.credentials_available:
                return False
                
            if self.sdk is None:
                return False
                
            # Try a simple SDK call to test connection
            user = self.sdk.me()
            return bool(user)
        except Exception as e:
            logging.error(f"Looker connection test failed: {e}")
            return False
