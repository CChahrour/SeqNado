"""
Tests for the bioconda recipe update script.
"""

import pytest
from pathlib import Path
import sys
import shutil

# Add the scripts directory to path so we can import the update script
sys.path.insert(0, str(Path(__file__).parent.parent.parent / ".github" / "scripts"))

from update_bioconda_recipe import (
    extract_jinja2_and_yaml,
    replace_jinja_expressions,
    restore_jinja_expressions,
    update_meta_yaml,
)

# Test output directory
TEST_OUTPUT_DIR = Path(__file__).parent.parent.parent / "test_output"


@pytest.fixture
def test_dir(request):
    """Create a test directory in test_output/ for this test."""
    test_name = request.node.name
    tmpdir = TEST_OUTPUT_DIR / test_name
    tmpdir.mkdir(parents=True, exist_ok=True)
    
    # Clean it first
    for item in tmpdir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    
    yield tmpdir
    
    # Don't delete - keep for inspection


class TestJinja2Extraction:
    """Test Jinja2 statement extraction from raw content."""
    
    def test_extract_jinja2_statements(self):
        """Should extract {% set ... %} statements."""
        content = '''{% set version = "1.0.0" %}
{% set build = "0" %}
package:
  name: seqnado
  version: {{ version }}
'''
        jinja_lines, yaml_content = extract_jinja2_and_yaml(content)
        
        assert len(jinja_lines) == 2
        assert 'version = "1.0.0"' in jinja_lines[0]
        assert 'build = "0"' in jinja_lines[1]
        assert "package:" in yaml_content
        assert "version: {{ version }}" in yaml_content
    
    def test_extract_no_jinja2(self):
        """Should handle content with no Jinja2 statements."""
        content = '''package:
  name: seqnado
  version: 1.0.0
'''
        jinja_lines, yaml_content = extract_jinja2_and_yaml(content)
        
        assert len(jinja_lines) == 0
        assert "package:" in yaml_content
    
    def test_extract_mixed_content(self):
        """Should handle mixed Jinja2 and YAML lines."""
        content = '''{% set version = "1.0.0" %}
package:
  name: seqnado
  version: {{ version }}
requirements:
  run:
    - python
'''
        jinja_lines, yaml_content = extract_jinja2_and_yaml(content)
        
        assert len(jinja_lines) == 1
        assert "python" in yaml_content
        assert "package:" in yaml_content


class TestJinja2ExpressionHandling:
    """Test replacement and restoration of Jinja2 expressions."""
    
    def test_replace_jinja_expressions(self):
        """Should replace {{ ... }} with placeholders."""
        yaml_content = "version: {{ version }}\nbuild: {{ build }}"
        
        modified, placeholders = replace_jinja_expressions(yaml_content)
        
        assert "__JINJA_0__" in modified
        assert "__JINJA_1__" in modified
        assert "{{ version }}" in placeholders.values()
        assert "{{ build }}" in placeholders.values()
    
    def test_replace_no_expressions(self):
        """Should handle content with no Jinja2 expressions."""
        yaml_content = "version: 1.0.0\nbuild: 0"
        
        modified, placeholders = replace_jinja_expressions(yaml_content)
        
        assert modified == yaml_content
        assert len(placeholders) == 0
    
    def test_restore_jinja_expressions(self):
        """Should restore expressions from placeholders."""
        text = "version: __JINJA_0__\nbuild: __JINJA_1__"
        placeholders = {
            "__JINJA_0__": "{{ version }}",
            "__JINJA_1__": "{{ build }}"
        }
        
        restored = restore_jinja_expressions(text, placeholders)
        
        assert "{{ version }}" in restored
        assert "{{ build }}" in restored
    
    def test_roundtrip_expressions(self):
        """Should preserve expressions through replace and restore."""
        original = "version: {{ version }}\nbuild: {{ build }}"
        
        modified, placeholders = replace_jinja_expressions(original)
        restored = restore_jinja_expressions(modified, placeholders)
        
        assert restored == original


class TestUpdateMetaYaml:
    """Test the full meta.yaml update function."""
    
    def test_update_basic_meta_yaml(self, test_dir):
        """Should update version, SHA256, and dependencies."""
        tmpdir = test_dir
        
        # Create meta.yaml
        meta_yaml = tmpdir / "meta.yaml"
        meta_yaml.write_text("""package:
  name: seqnado
  version: 1.0.0
source:
  sha256: old_hash
requirements:
  run:
    - python >=3.10
    - snakemake >8,<9
""")
        
        # Create meta_deps.txt
        meta_deps = tmpdir / "meta_deps.txt"
        meta_deps.write_text("""- python >=3.10
- snakemake >=9.12.0,<=9.14.5
- numpy >=1.24,<=2.1.0
""")
        
        # Change to temp directory and run update
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            update_meta_yaml("1.0.1", "new_hash_abc123", str(meta_deps))
        finally:
            os.chdir(original_cwd)
        
        # Verify updates
        updated = meta_yaml.read_text()
        assert "version: 1.0.1" in updated
        assert "sha256: new_hash_abc123" in updated
        assert "snakemake >=9.12.0,<=9.14.5" in updated
        assert "numpy >=1.24,<=2.1.0" in updated
        assert "snakemake >8,<9" not in updated
    
    def test_update_preserves_jinja2(self, test_dir):
        """Should preserve Jinja2 templating."""
        tmpdir = test_dir
        
        # Create meta.yaml with Jinja2
        meta_yaml = tmpdir / "meta.yaml"
        meta_yaml.write_text("""{% set version = "1.0.0" %}
package:
  name: seqnado
  version: {{ version }}
source:
  sha256: old_hash
  url: https://pypi.io/packages/source/s/seqnado/seqnado-{{ version }}.tar.gz
requirements:
  build:
    - {{ compiler('c') }}
  run:
    - python >=3.10
""")
        
        # Create meta_deps.txt
        meta_deps = tmpdir / "meta_deps.txt"
        meta_deps.write_text("- python >=3.10\n- numpy >=1.24,<=2.1.0\n")
        
        # Update
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            update_meta_yaml("1.0.1", "new_hash", str(meta_deps))
        finally:
            os.chdir(original_cwd)
        
        # Verify Jinja2 is preserved
        updated = meta_yaml.read_text()
        assert "{% set version" in updated
        assert "{{ version }}" in updated
        assert "{{ compiler('c') }}" in updated
        assert "version: 1.0.1" in updated  # Version should be updated in Jinja2
    
    def test_missing_meta_yaml_raises(self, test_dir):
        """Should raise FileNotFoundError if meta.yaml missing."""
        tmpdir = test_dir
        
        meta_deps = tmpdir / "meta_deps.txt"
        meta_deps.write_text("- python\n")
        
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            with pytest.raises(FileNotFoundError):
                update_meta_yaml("1.0.1", "hash", str(meta_deps))
        finally:
            os.chdir(original_cwd)
    
    def test_missing_meta_deps_raises(self, test_dir):
        """Should raise FileNotFoundError if meta_deps.txt missing."""
        tmpdir = test_dir
        
        meta_yaml = tmpdir / "meta.yaml"
        meta_yaml.write_text("package:\n  name: test\n")
        
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            with pytest.raises(FileNotFoundError):
                update_meta_yaml("1.0.1", "hash", "/nonexistent/meta_deps.txt")
        finally:
            os.chdir(original_cwd)
    
    def test_update_handles_dash_prefix_in_deps(self, test_dir):
        """Should handle deps with '- ' prefix in meta_deps.txt."""
        tmpdir = test_dir
        
        meta_yaml = tmpdir / "meta.yaml"
        meta_yaml.write_text("""package:
  name: seqnado
  version: 1.0.0
source:
  sha256: old
requirements:
  run:
    - python
""")
        
        meta_deps = tmpdir / "meta_deps.txt"
        meta_deps.write_text("- python >=3.10\n- numpy\n")
        
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            update_meta_yaml("1.0.1", "hash", str(meta_deps))
        finally:
            os.chdir(original_cwd)
        
        updated = meta_yaml.read_text()
        assert "- python >=3.10" in updated
        assert "- numpy" in updated


class TestIntegration:
    """Integration tests for complete workflow."""
    
    def test_complete_update_workflow(self, test_dir):
        """Should handle realistic bioconda meta.yaml update."""
        tmpdir = test_dir
        
        # Create realistic meta.yaml similar to bioconda
        meta_yaml = tmpdir / "meta.yaml"
        meta_yaml.write_text("""{% set version = "1.0.0" %}
{% set build = "0" %}

package:
  name: seqnado
  version: {{ version }}

source:
  url: https://pypi.io/packages/source/s/seqnado/seqnado-{{ version }}.tar.gz
  sha256: abc123def456

build:
  number: {{ build }}
  noarch: python

requirements:
  build:
    - python >=3.10
    - pip
  host:
    - python >=3.10
    - pip
  run:
    - python >=3.10
    - snakemake >8,<9
    - pyyaml
""")
        
        meta_deps = tmpdir / "meta_deps.txt"
        meta_deps.write_text("""- python >=3.10
- snakemake >=9.12.0,<=9.14.5
- pyyaml
- numpy >=1.24,<=2.1.0
- pandas >=2.0,<=2.3.3
""")
        
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            update_meta_yaml("1.0.1", "xyz789uvw", str(meta_deps))
        finally:
            os.chdir(original_cwd)
        
        updated = meta_yaml.read_text()
        
        # Verify all updates
        assert "version = \"1.0.1\"" in updated  # Jinja2 version updated
        assert "version: 1.0.1" in updated  # YAML version updated
        assert "sha256: xyz789uvw" in updated
        assert "snakemake >=9.12.0,<=9.14.5" in updated
        assert "numpy >=1.24,<=2.1.0" in updated
        assert "pandas >=2.0,<=2.3.3" in updated
        assert "snakemake >8,<9" not in updated
        
        # Verify Jinja2 still works
        assert "{% set version" in updated
        assert "{{ version }}" in updated
