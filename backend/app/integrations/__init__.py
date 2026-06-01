"""Pluggable external integrations (SMS gateway, government connectors).

Each integration is defined as a small Protocol with a stub default, so the
wiring exists and is tested without depending on a live third-party service.
Real providers (Twilio, ETDA 1212, Cyber Police 1441) implement the Protocol
and are selected via configuration.
"""
