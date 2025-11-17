#!/usr/bin/env python3
"""
Universe MCP - Data Validator
Validates scraped data against JSON schemas
"""

import json
import jsonschema
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict


PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
DATA_DIR = PROJECT_ROOT / "data"


class DataValidator:
    """Validates MCP data against schemas"""

    def __init__(self):
        self.schemas = self.load_schemas()
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)

    def load_schemas(self) -> Dict:
        """Load all JSON schemas"""
        schemas = {}
        for schema_file in SCHEMAS_DIR.glob("*.schema.json"):
            name = schema_file.stem.replace('.schema', '')
            with open(schema_file, 'r') as f:
                schemas[name] = json.load(f)
        return schemas

    def validate_file(self, file_path: Path, schema_name: str) -> Tuple[bool, List[str]]:
        """Validate a single file against schema"""
        errors = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate against schema
            schema = self.schemas.get(schema_name)
            if not schema:
                errors.append(f"Schema '{schema_name}' not found")
                return False, errors

            try:
                jsonschema.validate(data, schema)
            except jsonschema.ValidationError as e:
                errors.append(f"Schema validation error: {e.message}")
                return False, errors

            # Additional custom validations
            if schema_name == 'server':
                # Check if required fields are meaningful
                if not data.get('name') or data['name'] == 'Unknown':
                    self.warnings[file_path].append("Server name is 'Unknown'")
                if not data.get('description'):
                    self.warnings[file_path].append("Missing description")

        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {e}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected error: {e}")
            return False, errors

        return True, errors

    def validate_directory(self, directory: Path, schema_name: str) -> Dict:
        """Validate all files in a directory"""
        if not directory.exists():
            return {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'errors': [],
                'warnings': []
            }

        files = list(directory.glob("**/*.json"))
        valid_count = 0
        invalid_count = 0
        all_errors = []

        for file_path in files:
            is_valid, errors = self.validate_file(file_path, schema_name)
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                all_errors.append({
                    'file': str(file_path.relative_to(PROJECT_ROOT)),
                    'errors': errors
                })

        return {
            'total': len(files),
            'valid': valid_count,
            'invalid': invalid_count,
            'errors': all_errors,
            'warnings': list(self.warnings.values())
        }

    def run(self) -> Dict:
        """Run validation on all data"""
        print("=" * 80)
        print("🔍 UNIVERSE MCP - Data Validation")
        print("=" * 80)

        results = {}

        # Validate servers
        print("\n📦 Validating servers...")
        results['servers'] = self.validate_directory(
            DATA_DIR / "servers",
            'server'
        )
        print(f"  ✅ Valid: {results['servers']['valid']}")
        print(f"  ❌ Invalid: {results['servers']['invalid']}")
        print(f"  📊 Total: {results['servers']['total']}")

        # Validate clients
        print("\n📦 Validating clients...")
        results['clients'] = self.validate_directory(
            DATA_DIR / "clients",
            'client'
        )
        print(f"  ✅ Valid: {results['clients']['valid']}")
        print(f"  ❌ Invalid: {results['clients']['invalid']}")
        print(f"  📊 Total: {results['clients']['total']}")

        # Validate use cases
        print("\n📦 Validating use cases...")
        results['use-cases'] = self.validate_directory(
            DATA_DIR / "use-cases",
            'usecase'
        )
        print(f"  ✅ Valid: {results['use-cases']['valid']}")
        print(f"  ❌ Invalid: {results['use-cases']['invalid']}")
        print(f"  📊 Total: {results['use-cases']['total']}")

        # Print detailed errors if any
        total_invalid = sum(r['invalid'] for r in results.values())
        if total_invalid > 0:
            print("\n" + "=" * 80)
            print("❌ VALIDATION ERRORS")
            print("=" * 80)
            for category, result in results.items():
                if result['errors']:
                    print(f"\n{category.upper()}:")
                    for error in result['errors'][:10]:  # Show first 10
                        print(f"  📄 {error['file']}")
                        for err in error['errors']:
                            print(f"     - {err}")
                    if len(result['errors']) > 10:
                        print(f"  ... and {len(result['errors']) - 10} more errors")

        # Summary
        print("\n" + "=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        total_files = sum(r['total'] for r in results.values())
        total_valid = sum(r['valid'] for r in results.values())
        total_invalid = sum(r['invalid'] for r in results.values())

        print(f"Total files: {total_files}")
        print(f"Valid: {total_valid} ({total_valid/total_files*100:.1f}%)" if total_files > 0 else "Valid: 0")
        print(f"Invalid: {total_invalid} ({total_invalid/total_files*100:.1f}%)" if total_files > 0 else "Invalid: 0")

        if total_invalid == 0:
            print("\n✅ All files passed validation!")
        else:
            print(f"\n⚠️  {total_invalid} files failed validation")

        print("=" * 80)

        return results


def main():
    """Main entry point"""
    validator = DataValidator()
    results = validator.run()

    # Exit with error code if validation failed
    total_invalid = sum(r['invalid'] for r in results.values())
    exit(0 if total_invalid == 0 else 1)


if __name__ == '__main__':
    main()
