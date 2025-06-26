"""
Webex People management tools.
"""
from typing import Optional, Dict, Any
from .common import webex_api


def get_webex_me() -> Dict[str, Any]:
    """
    Get information about the authenticated Webex user.
    
    Returns:
        Dictionary containing the authenticated user's information
    """
    try:
        # Call the Webex API to get user info
        me_response = webex_api.people.me()
        
        # Convert the response to a dictionary
        me_dict = {
            'id': me_response.id,
            'emails': me_response.emails,
            'displayName': me_response.displayName,
            'nickName': me_response.nickName,
            'firstName': me_response.firstName,
            'lastName': me_response.lastName,
            'avatar': me_response.avatar,
            'orgId': me_response.orgId,
            'created': me_response.created,
            'lastModified': me_response.lastModified,
            'status': me_response.status,
            'type': me_response.type
        }
        
        # Add optional fields if they exist
        if hasattr(me_response, 'userName') and me_response.userName:
            me_dict['userName'] = me_response.userName
        if hasattr(me_response, 'roles') and me_response.roles:
            me_dict['roles'] = me_response.roles
        if hasattr(me_response, 'licenses') and me_response.licenses:
            me_dict['licenses'] = me_response.licenses
        if hasattr(me_response, 'phoneNumbers') and me_response.phoneNumbers:
            me_dict['phoneNumbers'] = me_response.phoneNumbers
        if hasattr(me_response, 'extension') and me_response.extension:
            me_dict['extension'] = me_response.extension
        if hasattr(me_response, 'locationId') and me_response.locationId:
            me_dict['locationId'] = me_response.locationId
        if hasattr(me_response, 'addresses') and me_response.addresses:
            me_dict['addresses'] = me_response.addresses
        if hasattr(me_response, 'timezone') and me_response.timezone:
            me_dict['timezone'] = me_response.timezone
        
        return {
            'success': True,
            'user': me_dict
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'user': None
        }


def list_webex_people(
    email: Optional[str] = None,
    display_name: Optional[str] = None,
    id: Optional[str] = None,
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
        id: Person ID to get specific person
        org_id: Organization ID to filter by
        calling_data: Include calling data in response
        location_id: Location ID to filter by
        max_results: Maximum number of people to return (default 100, max 1000)
    
    Returns:
        Dictionary containing the list of people and metadata
    """
    try:
        # Build parameters dict
        params = {}
        if email:
            params['email'] = email
        if display_name:
            params['displayName'] = display_name
        if id:
            params['id'] = id
        if org_id:
            params['orgId'] = org_id
        if calling_data is not None:
            params['callingData'] = calling_data
        if location_id:
            params['locationId'] = location_id
        if max_results:
            params['max'] = max_results
        
        # Call the Webex API
        people_response = webex_api.people.list(**params)
        
        # Convert the response to a list of dictionaries
        people_list = []
        for person in people_response:
            person_dict = {
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
                'type': person.type
            }
            
            # Add optional fields if they exist
            if hasattr(person, 'userName') and person.userName:
                person_dict['userName'] = person.userName
            if hasattr(person, 'lastModified') and person.lastModified:
                person_dict['lastModified'] = person.lastModified
            if hasattr(person, 'roles') and person.roles:
                person_dict['roles'] = person.roles
            if hasattr(person, 'licenses') and person.licenses:
                person_dict['licenses'] = person.licenses
            if hasattr(person, 'phoneNumbers') and person.phoneNumbers:
                person_dict['phoneNumbers'] = person.phoneNumbers
            if hasattr(person, 'extension') and person.extension:
                person_dict['extension'] = person.extension
            if hasattr(person, 'locationId') and person.locationId:
                person_dict['locationId'] = person.locationId
            if hasattr(person, 'addresses') and person.addresses:
                person_dict['addresses'] = person.addresses
            if hasattr(person, 'timezone') and person.timezone:
                person_dict['timezone'] = person.timezone
                
            people_list.append(person_dict)
        
        return {
            'success': True,
            'people': people_list,
            'count': len(people_list),
            'filters_applied': params
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'people': [],
            'count': 0
        }
