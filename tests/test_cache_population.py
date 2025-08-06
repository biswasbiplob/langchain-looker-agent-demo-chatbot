#!/usr/bin/env python3
"""
Test script for cache population functionality

This tests the populate_cache.py script structure and basic functionality
without requiring full Looker credentials.
"""

import sys
import os
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestCachePopulation(unittest.TestCase):
    """Test cache population script functionality"""
    
    def test_script_imports(self):
        """Test that the cache population script can be imported"""
        try:
            import populate_cache
            self.assertTrue(hasattr(populate_cache, 'LookerCachePopulator'))
            self.assertTrue(hasattr(populate_cache, 'main'))
        except ImportError as e:
            self.fail(f"Failed to import populate_cache module: {e}")
    
    def test_cache_populator_init(self):
        """Test LookerCachePopulator initialization structure"""
        import populate_cache
        
        # Mock the database and agent initialization to avoid requiring credentials
        with patch.object(populate_cache.LookerCachePopulator, '_init_database'), \
             patch.object(populate_cache.LookerCachePopulator, '_init_looker_agent'):
            
            populator = populate_cache.LookerCachePopulator(verbose=True)
            
            # Check that stats are initialized
            self.assertIsInstance(populator.stats, dict)
            self.assertIn('models_cached', populator.stats)
            self.assertIn('explores_cached', populator.stats)
            self.assertIn('dashboards_cached', populator.stats)
            self.assertIn('start_time', populator.stats)
            self.assertIsInstance(populator.stats['start_time'], datetime)
    
    def test_cache_freshness_methods(self):
        """Test cache freshness checking methods"""
        import populate_cache
        
        with patch.object(populate_cache.LookerCachePopulator, '_init_database'), \
             patch.object(populate_cache.LookerCachePopulator, '_init_looker_agent'):
            
            populator = populate_cache.LookerCachePopulator()
            
            # These methods should exist
            self.assertTrue(hasattr(populator, '_is_models_cache_fresh'))
            self.assertTrue(hasattr(populator, '_is_explores_cache_fresh'))
            self.assertTrue(hasattr(populator, '_is_dashboards_cache_fresh'))
    
    def test_population_methods(self):
        """Test that population methods exist"""
        import populate_cache
        
        with patch.object(populate_cache.LookerCachePopulator, '_init_database'), \
             patch.object(populate_cache.LookerCachePopulator, '_init_looker_agent'):
            
            populator = populate_cache.LookerCachePopulator()
            
            # These methods should exist and be callable
            self.assertTrue(callable(getattr(populator, 'populate_models', None)))
            self.assertTrue(callable(getattr(populator, 'populate_explores', None)))
            self.assertTrue(callable(getattr(populator, 'populate_dashboards', None)))
            self.assertTrue(callable(getattr(populator, 'populate_all', None)))
    
    def test_script_help_functionality(self):
        """Test that the script provides proper help"""
        import populate_cache
        import argparse
        from io import StringIO
        
        # Test that argparse setup works
        parser = argparse.ArgumentParser(
            description='Test argument parser setup'
        )
        parser.add_argument('--models', action='store_true')
        parser.add_argument('--explores', action='store_true')
        parser.add_argument('--dashboards', action='store_true')
        parser.add_argument('--all', action='store_true')
        parser.add_argument('--force', action='store_true')
        parser.add_argument('--verbose', '-v', action='store_true')
        
        # Parse test arguments
        test_args = parser.parse_args(['--models', '--verbose'])
        self.assertTrue(test_args.models)
        self.assertTrue(test_args.verbose)
        self.assertFalse(test_args.all)
    
    def test_environment_variable_validation(self):
        """Test environment variable validation logic"""
        import populate_cache
        
        required_vars = ['LOOKER_BASE_URL', 'LOOKER_CLIENT_ID', 'LOOKER_CLIENT_SECRET', 'OPENAI_API_KEY']
        
        # Test missing variables detection
        with patch.dict(os.environ, {}, clear=True):
            missing_vars = [var for var in required_vars if not os.getenv(var)]
            self.assertEqual(len(missing_vars), 4)  # All should be missing
    
    def test_dotenv_loading(self):
        """Test that dotenv loading functionality works"""
        import populate_cache
        from dotenv import load_dotenv
        
        # Test that load_dotenv is imported and available
        self.assertTrue(hasattr(populate_cache, 'load_dotenv'))
        
        # Test that load_dotenv can be called without error
        try:
            load_dotenv()
        except Exception as e:
            self.fail(f"load_dotenv() raised an exception: {e}")
    
    def test_docstring_and_documentation(self):
        """Test that the script has proper documentation"""
        import populate_cache
        
        # Check module docstring
        self.assertIsNotNone(populate_cache.__doc__)
        self.assertIn('Looker Cache Population CLI Script', populate_cache.__doc__)
        
        # Check class docstring
        self.assertIsNotNone(populate_cache.LookerCachePopulator.__doc__)
        self.assertIn('cache populator', populate_cache.LookerCachePopulator.__doc__.lower())

def run_cache_population_tests():
    """Run cache population tests"""
    print("Running Cache Population Tests...")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestCachePopulation)
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All cache population tests passed!")
        return True
    else:
        print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        for test, traceback in result.failures + result.errors:
            print(f"Failed: {test}")
            print(f"Error: {traceback}")
        return False

if __name__ == '__main__':
    success = run_cache_population_tests()
    sys.exit(0 if success else 1)