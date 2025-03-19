import pytest
from unittest.mock import patch, MagicMock
import sys
import os

# Agregar el directorio principal al path para importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui import format_status_class, format_job_status

def test_format_status_class():
    """Test the format_status_class function"""
    assert format_status_class("healthy") == "status-healthy"
    assert format_status_class("degraded") == "status-degraded"
    assert format_status_class("error") == "status-error"
    assert format_status_class("unknown") == "status-error"

def test_format_job_status():
    """Test the format_job_status function"""
    assert "job-success" in format_job_status("completed", "success")
    assert "job-failure" in format_job_status("completed", "failure")
    assert "job-in-progress" in format_job_status("in_progress", None)
    assert "N/A" in format_job_status("queued", None)
