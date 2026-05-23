"""
Webex People management tools.
"""
from typing import Optional, Dict, Any
from .common import get_webex_api, create_error_response, create_success_response, WebexErrorCodes, WebexTokenMissingError


def _map_exception_to_error(e: Exception) -> Dict[str, Any]:
    if isinstance(e, WebexTokenMissingError):
        return create_error_response(WebexErrorCodes.UNAUTHORIZED, str(e))
    error_str = str(e).lower()
    if 'unauthorized' in error_str or 'invalid token' in error_str:
        return create_error_response(WebexErrorCodes.UNAUTHORIZED,
                                     "Invalid or expired bot token.")
    if 'not found' in error_str or '404' in error_str:
        return create_error_response(WebexErrorCodes.NOT_FOUND,
                                     "Person not found. Verify the ID or email is correct.")
    if 'forbidden' in error_str or '403' in error_str:
        return create_error_response(WebexErrorCodes.FORBIDDEN,
                                     "Bot lacks permission for this operation.")
    if 'rate limit' in error_str or 'too many requests' in error_str:
        return create_error_response(WebexErrorCodes.RATE_LIMITED,
                                     "API rate limit exceeded. Please retry after delay.",
                                     temporary=True, retry_after_seconds=60)
    if 'network' in error_str or 'connection' in error_str:
        return create_error_response(WebexErrorCodes.NETWORK_ERROR,
                                     "Network connectivity issue. Please retry.",
                                     temporary=True, retry_after_seconds=30)
    return create_error_response(WebexErrorCodes.WEBEX_API_ERROR,
                                 f"Webex API error: {e}",
                                 temporary=True, details={'original_error': str(e)})


def _person_to_dict(person) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        'id': person.id,
        'emails': person.emails,
        'displayName': person.displayName,
        'nickName': person.nickName,
        'firstName': person.firstName,
        'lastName': person.lastName,
        'avatar': person.avatar,
        'orgId': person.orgId,
        'created': person.created,
        'status': person.status,
        'type': person.type,
    }
    for attr in ('userName', 'lastModified', 'roles', 'licenses',
                 'phoneNumbers', 'extension', 'locationId', 'addresses', 'timezone'):
        val = getattr(person, attr, None)
        if val:
            d[attr] = val
    return d


def get_webex_me() -> Dict[str, Any]:
    """
    Get information about the authenticated Webex bot.

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        me = get_webex_api().people.me()
        return create_success_response(data={'user': _person_to_dict(me)})
    except Exception as e:
        return _map_exception_to_error(e)


def list_webex_people(
    email: Optional[str] = None,
    display_name: Optional[str] = None,
    person_id: Optional[str] = None,
    org_id: Optional[str] = None,
    calling_data: Optional[bool] = None,
    location_id: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    List people in the organization or search for specific people.

    Args:
        email: Email address to search for
        display_name: Display name to search for
        person_id: Person ID to look up a specific person
        org_id: Organization ID to filter by
        calling_data: Include calling data in response
        location_id: Location ID to filter by
        max_results: Maximum number of people to return (default 100, max 1000)

    Returns:
        Standardized response dictionary with success/error information
    """
    try:
        params: Dict[str, Any] = {}
        if email:
            params['email'] = email
        if display_name:
            params['displayName'] = display_name
        if person_id:
            params['id'] = person_id
        if org_id:
            params['orgId'] = org_id
        if calling_data is not None:
            params['callingData'] = calling_data
        if location_id:
            params['locationId'] = location_id
        if max_results:
            params['max'] = max_results

        people = [_person_to_dict(p) for p in get_webex_api().people.list(**params)]
        return create_success_response(
            data={'people': people},
            metadata={'count': len(people), 'filters_applied': params}
        )
    except Exception as e:
        return _map_exception_to_error(e)
