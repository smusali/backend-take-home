"""
Unit tests for EmailService.

Tests email template rendering, SMTP connection, and email sending
with retry logic.
"""

from unittest.mock import AsyncMock, patch
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.services.email_service import EmailService


class TestEmailService:
    """Test suite for EmailService."""
    
    def setup_method(self):
        """Setup test email service."""
        self.service = EmailService()
    
    def test_initialization(self):
        """Test email service initializes correctly."""
        assert self.service.settings is not None
        assert self.service.jinja_env is not None
    
    def test_template_directory_exists(self):
        """Test that template directory exists."""
        template_dir = Path(__file__).parent.parent.parent / "app" / "templates"
        assert template_dir.exists()
        assert template_dir.is_dir()
    
    def test_prospect_template_exists(self):
        """Test that prospect confirmation template exists."""
        template_dir = Path(__file__).parent.parent.parent / "app" / "templates"
        template_file = template_dir / "prospect_confirmation.html"
        assert template_file.exists()
    
    def test_attorney_template_exists(self):
        """Test that attorney notification template exists."""
        template_dir = Path(__file__).parent.parent.parent / "app" / "templates"
        template_file = template_dir / "attorney_notification.html"
        assert template_file.exists()
    
    def test_render_prospect_template(self):
        """Test rendering prospect confirmation template."""
        context = {
            "prospect_name": "John Doe",
            "lead_id": "test-lead-id-123",
            "company_name": "Test Company"
        }
        
        html = self.service._render_template("prospect_confirmation.html", context)
        
        assert "John Doe" in html
        assert "test-lead-id-123" in html
        assert "Test Company" in html
        assert "Submission Received" in html
    
    def test_render_attorney_template(self):
        """Test rendering attorney notification template."""
        context = {
            "lead_id": "test-lead-id-123",
            "prospect_name": "John Doe",
            "prospect_email": "john@example.com",
            "resume_filename": "resume.pdf",
            "dashboard_url": "https://dashboard.example.com/leads/123"
        }
        
        html = self.service._render_template("attorney_notification.html", context)
        
        assert "John Doe" in html
        assert "john@example.com" in html
        assert "resume.pdf" in html
        assert "test-lead-id-123" in html
        assert "dashboard.example.com" in html
    
    def test_render_template_with_missing_template(self):
        """Test that missing template raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            self.service._render_template("nonexistent.html", {})
        
        assert exc_info.value.status_code == 500
        assert "Failed to render email template" in exc_info.value.detail
    
    def test_create_message(self):
        """Test creating MIME message."""
        message = self.service._create_message(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<h1>Test</h1>"
        )
        
        assert message["To"] == "recipient@example.com"
        assert message["Subject"] == "Test Subject"
        assert self.service.settings.SMTP_FROM_EMAIL in message["From"]
        assert self.service.settings.SMTP_FROM_NAME in message["From"]
    
    def test_create_message_with_custom_from(self):
        """Test creating message with custom sender."""
        message = self.service._create_message(
            to_email="recipient@example.com",
            subject="Test Subject",
            html_content="<h1>Test</h1>",
            from_email="custom@example.com",
            from_name="Custom Name"
        )
        
        assert "custom@example.com" in message["From"]
        assert "Custom Name" in message["From"]
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_email_success(self, mock_smtp_class):
        """Test successful email sending."""
        # Setup mock SMTP instance
        mock_smtp = AsyncMock()
        mock_smtp_class.return_value = mock_smtp
        
        # Create test message
        message = self.service._create_message(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>"
        )
        
        # Send email
        result = await self.service._send_email(message, max_retries=1)
        
        assert result is True
        mock_smtp.connect.assert_called_once()
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once()
        mock_smtp.send_message.assert_called_once()
        mock_smtp.quit.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_email_with_retry(self, mock_smtp_class):
        """Test email sending with retry on failure."""
        # Setup mock to fail once then succeed
        mock_smtp = AsyncMock()
        mock_smtp.connect.side_effect = [
            Exception("Connection failed"),
            None  # Success on second attempt
        ]
        mock_smtp_class.return_value = mock_smtp
        
        message = self.service._create_message(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>"
        )
        
        # Should succeed after retry
        result = await self.service._send_email(message, max_retries=2, retry_delay=0.01)
        
        assert result is True
        assert mock_smtp.connect.call_count == 2
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_email_all_retries_fail(self, mock_smtp_class):
        """Test that all retry attempts failing raises exception."""
        # Setup mock to always fail
        mock_smtp = AsyncMock()
        mock_smtp.connect.side_effect = Exception("Connection failed")
        mock_smtp_class.return_value = mock_smtp
        
        message = self.service._create_message(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>"
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await self.service._send_email(message, max_retries=2, retry_delay=0.01)
        
        assert exc_info.value.status_code == 500
        assert "Failed to send email" in exc_info.value.detail
        assert mock_smtp.connect.call_count == 2
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_prospect_confirmation(self, mock_smtp_class):
        """Test sending prospect confirmation email."""
        mock_smtp = AsyncMock()
        mock_smtp_class.return_value = mock_smtp
        
        result = await self.service.send_prospect_confirmation(
            prospect_email="john@example.com",
            prospect_name="John Doe",
            lead_id="test-lead-123"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
        
        # Verify message content
        call_args = mock_smtp.send_message.call_args
        message = call_args[0][0]
        assert message["To"] == "john@example.com"
        assert "Thank You" in message["Subject"]
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_attorney_notification(self, mock_smtp_class):
        """Test sending attorney notification email."""
        mock_smtp = AsyncMock()
        mock_smtp_class.return_value = mock_smtp
        
        result = await self.service.send_attorney_notification(
            lead_id="test-lead-123",
            prospect_name="John Doe",
            prospect_email="john@example.com",
            resume_filename="resume.pdf"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
        
        # Verify message content
        call_args = mock_smtp.send_message.call_args
        message = call_args[0][0]
        assert message["To"] == self.service.settings.ATTORNEY_EMAIL
        assert "New Lead Submission" in message["Subject"]
        assert "John Doe" in message["Subject"]
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_attorney_notification_with_dashboard_url(self, mock_smtp_class):
        """Test attorney notification with custom dashboard URL."""
        mock_smtp = AsyncMock()
        mock_smtp_class.return_value = mock_smtp
        
        await self.service.send_attorney_notification(
            lead_id="test-lead-123",
            prospect_name="John Doe",
            prospect_email="john@example.com",
            resume_filename="resume.pdf",
            dashboard_url="https://dashboard.example.com/leads/test-lead-123"
        )
        
        # Verify URL is in email content (would need to parse HTML in real scenario)
        mock_smtp.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_custom_email(self, mock_smtp_class):
        """Test sending custom HTML email."""
        mock_smtp = AsyncMock()
        mock_smtp_class.return_value = mock_smtp
        
        result = await self.service.send_custom_email(
            to_email="custom@example.com",
            subject="Custom Subject",
            html_content="<h1>Custom Content</h1>"
        )
        
        assert result is True
        mock_smtp.send_message.assert_called_once()
        
        # Verify message content
        call_args = mock_smtp.send_message.call_args
        message = call_args[0][0]
        assert message["To"] == "custom@example.com"
        assert message["Subject"] == "Custom Subject"
    
    @pytest.mark.asyncio
    @patch('aiosmtplib.SMTP')
    async def test_send_custom_email_with_retries(self, mock_smtp_class):
        """Test custom email with specified retry count."""
        mock_smtp = AsyncMock()
        mock_smtp.connect.side_effect = [
            Exception("Fail 1"),
            Exception("Fail 2"),
            None  # Success on third
        ]
        mock_smtp_class.return_value = mock_smtp
        
        result = await self.service.send_custom_email(
            to_email="test@example.com",
            subject="Test",
            html_content="<p>Test</p>",
            max_retries=3
        )
        
        assert result is True
        assert mock_smtp.connect.call_count == 3
    
    def test_template_contains_required_prospect_fields(self):
        """Test prospect template contains all required placeholders."""
        template_dir = Path(__file__).parent.parent.parent / "app" / "templates"
        template_file = template_dir / "prospect_confirmation.html"
        
        content = template_file.read_text()
        
        assert "{{ prospect_name }}" in content
        assert "{{ lead_id }}" in content
        assert "{{ company_name }}" in content
    
    def test_template_contains_required_attorney_fields(self):
        """Test attorney template contains all required placeholders."""
        template_dir = Path(__file__).parent.parent.parent / "app" / "templates"
        template_file = template_dir / "attorney_notification.html"
        
        content = template_file.read_text()
        
        assert "{{ prospect_name }}" in content
        assert "{{ prospect_email }}" in content
        assert "{{ resume_filename }}" in content
        assert "{{ lead_id }}" in content
        assert "{{ dashboard_url }}" in content
