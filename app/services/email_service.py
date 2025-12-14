"""
Email service for sending notifications to prospects and attorneys.

Handles SMTP connection, template rendering, and async email delivery
with retry logic and error handling.
"""

import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader

from fastapi import HTTPException, status

from app.core.config import get_settings


class EmailService:
    """
    Service for sending HTML emails using SMTP.
    
    Handles template rendering, SMTP connection, and async email delivery
    with automatic retry logic.
    """
    
    def __init__(self):
        """Initialize email service with configuration and template engine."""
        self.settings = get_settings()
        
        # Setup Jinja2 template engine
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )
    
    def _render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render an email template with context data.
        
        Args:
            template_name: Name of the template file
            context: Dictionary of template variables
            
        Returns:
            Rendered HTML string
            
        Raises:
            HTTPException: If template not found or rendering fails
        """
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to render email template: {str(e)}"
            )
    
    def _create_message(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> MIMEMultipart:
        """
        Create a MIME multipart email message.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML content of the email
            from_email: Sender email (defaults to configured SMTP_FROM_EMAIL)
            from_name: Sender name (defaults to configured SMTP_FROM_NAME)
            
        Returns:
            MIMEMultipart message ready to send
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = f"{from_name or self.settings.SMTP_FROM_NAME} <{from_email or self.settings.SMTP_FROM_EMAIL}>"
        message["To"] = to_email
        
        # Attach HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        return message
    
    async def _send_email(
        self,
        message: MIMEMultipart,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> bool:
        """
        Send email via SMTP with retry logic.
        
        Args:
            message: MIMEMultipart message to send
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            True if email sent successfully
            
        Raises:
            HTTPException: If all retry attempts fail
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Create SMTP client
                smtp = aiosmtplib.SMTP(
                    hostname=self.settings.SMTP_HOST,
                    port=self.settings.SMTP_PORT,
                    use_tls=False
                )
                
                # Connect and authenticate
                await smtp.connect()
                await smtp.starttls()
                await smtp.login(
                    self.settings.SMTP_USERNAME,
                    self.settings.SMTP_PASSWORD
                )
                
                # Send message
                await smtp.send_message(message)
                await smtp.quit()
                
                return True
                
            except Exception as e:
                last_error = e
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay * (attempt + 1))
                    continue
        
        # All retries failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email after {max_retries} attempts: {str(last_error)}"
        )
    
    async def send_prospect_confirmation(
        self,
        prospect_email: str,
        prospect_name: str,
        lead_id: str
    ) -> bool:
        """
        Send confirmation email to prospect after lead submission.
        
        Args:
            prospect_email: Prospect's email address
            prospect_name: Prospect's full name
            lead_id: UUID of the created lead
            
        Returns:
            True if email sent successfully
            
        Raises:
            HTTPException: If email sending fails
            
        Example:
            >>> await service.send_prospect_confirmation(
            ...     "john@example.com",
            ...     "John Doe",
            ...     "a1b2c3d4-..."
            ... )
        """
        context = {
            "prospect_name": prospect_name,
            "lead_id": lead_id,
            "company_name": self.settings.SMTP_FROM_NAME,
        }
        
        html_content = self._render_template(
            "prospect_confirmation.html",
            context
        )
        
        message = self._create_message(
            to_email=prospect_email,
            subject="Thank You for Your Submission",
            html_content=html_content
        )
        
        return await self._send_email(message)
    
    async def send_attorney_notification(
        self,
        lead_id: str,
        prospect_name: str,
        prospect_email: str,
        resume_filename: str,
        dashboard_url: Optional[str] = None
    ) -> bool:
        """
        Send notification email to attorney about new lead.
        
        Args:
            lead_id: UUID of the created lead
            prospect_name: Prospect's full name
            prospect_email: Prospect's email address
            resume_filename: Name of uploaded resume file
            dashboard_url: Optional URL to lead in dashboard
            
        Returns:
            True if email sent successfully
            
        Raises:
            HTTPException: If email sending fails
            
        Example:
            >>> await service.send_attorney_notification(
            ...     "a1b2c3d4-...",
            ...     "John Doe",
            ...     "john@example.com",
            ...     "resume.pdf",
            ...     "https://dashboard.example.com/leads/a1b2c3d4-..."
            ... )
        """
        context = {
            "lead_id": lead_id,
            "prospect_name": prospect_name,
            "prospect_email": prospect_email,
            "resume_filename": resume_filename,
            "dashboard_url": dashboard_url or f"/leads/{lead_id}",
        }
        
        html_content = self._render_template(
            "attorney_notification.html",
            context
        )
        
        message = self._create_message(
            to_email=self.settings.ATTORNEY_EMAIL,
            subject=f"New Lead Submission: {prospect_name}",
            html_content=html_content
        )
        
        return await self._send_email(message)
    
    async def send_custom_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        max_retries: int = 3
    ) -> bool:
        """
        Send a custom HTML email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML content of the email
            max_retries: Maximum retry attempts
            
        Returns:
            True if email sent successfully
            
        Raises:
            HTTPException: If email sending fails
        """
        message = self._create_message(
            to_email=to_email,
            subject=subject,
            html_content=html_content
        )
        
        return await self._send_email(message, max_retries=max_retries)


__all__ = ["EmailService"]
