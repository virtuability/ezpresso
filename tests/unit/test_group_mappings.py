
from sso.group_mappings import GroupMappings

def test_group_mappings():

    group_prefix = 'PR_AWS_SSO_'

    group_mappings_raw = {
        'group_mappings': [
            {
                'group_id' : '1234567890-12345678-1230-1230-1230-123456789012',
                'group_name' : 'PR_AWS_SSO_Development',
            },
            {
                'group_id' : '2345678911-12345678-1230-1230-1230-123456789012',
                'group_name' : 'PR_AWS_SSO_Production',
            },
        ]
    }

    group_mappings = GroupMappings(group_prefix, group_mappings_raw)

    assert group_mappings.get_group_mappings() == group_mappings_raw['group_mappings']

    mapping = group_mappings.get_mapping_by_name('Development')
    assert mapping == {
        'group_id' : '1234567890-12345678-1230-1230-1230-123456789012',
        'group_name' : group_prefix + 'Development',
    }
