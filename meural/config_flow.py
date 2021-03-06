"""Config flow for Meural integration."""
import asyncio
import aiohttp
import logging

import voluptuous as vol

from homeassistant import config_entries, core, exceptions

from .const import DOMAIN  # pylint:disable=unused-import

from . import pymeural

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({"email": str, "password": str})


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    session = hass.helpers.aiohttp_client.async_get_clientsession()
    try:
        token = await pymeural.authenticate(session, data["email"], data["password"])
    except (aiohttp.ClientError, asyncio.TimeoutError):
        raise CannotConnect

    return token


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meural."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                token = await validate_input(self.hass, user_input)

                return self.async_create_entry(
                    title=user_input["email"],
                    data={"email": user_input["email"], "token": token},
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
