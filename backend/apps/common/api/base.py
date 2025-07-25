#! Base api view to handle both json and html renderer
from typing import Optional, Dict, Any, Union,List

from django.contrib import messages
from django.shortcuts import redirect
from django.http import HttpResponseRedirect

from rest_framework.views import APIView
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework import status
import logging
logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    renderer_classes = [JSONRenderer, TemplateHTMLRenderer]
    MESSAGE_KEY = 'message'  # Central key for API messages
    ERRORS_KEY = 'errors'    # Central key for error details
    template_map = {}        # Map of view methods to template paths or redirects

    def get_template_name(self, method: str) -> Optional[str]:
        """Resolve template name for the given HTTP method from template_map."""
        view_name = self.__class__.__name__
        # Check for method-specific template (e.g., 'POST': 'template.html')
        template = self.template_map.get(method.upper())
        # Fallback to view-level template (e.g., 'DEFAULT': 'template.html')
        template = template or self.template_map.get('DEFAULT')
        # Fallback to template_name if defined
        template = template or getattr(self, 'template_name', None)
        if not template:
            logger.warning(f"No template defined for {view_name}.{method}")
        return template
    
    def render_response(
        self,
        *,
        data: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_200_OK,
        template_name: Optional[str] = None,
        message: Optional[str] = None,
        errors: Optional[Union[Dict, List]] = None,
        message_level: str = 'success',
        html_context: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, Any]] = None,
    ) -> Union[Response, HttpResponseRedirect]:
        """
        Centralized response builder for both JSON and HTML.

        :param data: Core payload for JSON/HTML.
        :param status_code: HTTP status code.
        :param template_name: Template path or 'redirect:<url>'.
        :param message: Flash message text (HTML only).
        :param message_level: One of 'success', 'error', etc. (HTML only).
        :param html_context: Additional context keys for HTML rendering.
        :param headers: Custom headers to attach to the response.
        :param cookies: Cookies to set on the response.
        :return: DRF Response or Django redirect.
        """
        payload: Dict[str, Any] = dict(data or {})


        # Add message to payload for all clients
        if message:
            payload[self.MESSAGE_KEY] = message

        
        # Add error details to payload for API clients
        if errors:
            payload[self.ERRORS_KEY] = errors

        # Resolve template dynamically if not provided
        if not template_name:
            template_name = self.get_template_name(self.request.method)

        # HTML-render path
        if self.request.accepted_renderer.format == 'html':
            if message:
                getattr(messages, message_level)(self.request, message)  # type: ignore

            if html_context:
                payload.update(html_context)

            # Handle redirect shortcuts
            if template_name and template_name.startswith('redirect:'):
                target_url = template_name.replace('redirect:', '')
                return redirect(target_url)
            
             # For error cases, include errors in context
            if errors:
                payload[self.ERRORS_KEY] = errors

            response = Response(
                data=payload,
                template_name=template_name,
                status=status_code,
            )
        else:
            # JSON-render path
            response = Response(
                data=payload,
                status=status_code,
            )

        # Attach headers if provided
        if headers:
            for header_name, header_value in headers.items():
                response[header_name] = header_value

        # Attach cookies if provided
        if cookies:
            for cookie_name, cookie_value in cookies.items():
                response.set_cookie(cookie_name, cookie_value)

        return response