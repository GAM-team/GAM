"""Tests for gam.cmd.gelicenses — Gemini Enterprise license management.

Tests cover:
- Path/parent construction helpers
- LRO result handling
- Subscription resolution logic
- Batch update body construction
- Error handling with IAM guidance
- Sync delta computation
- buildGAPIObjectGE endpoint selection and credential wiring
- Dispatch table wiring
- Message string validation
"""

import json
import sys
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Pure helpers — no mocking needed
# ---------------------------------------------------------------------------

class TestGetGEParent:
    """_getGEParent builds the correct userStore resource path."""

    def test_global_location(self):
        from gam.cmd.gelicenses import _getGEParent
        assert _getGEParent('123456', 'global') == \
            'projects/123456/locations/global/userStores/default_user_store'

    def test_regional_location(self):
        from gam.cmd.gelicenses import _getGEParent
        assert _getGEParent('999', 'us') == \
            'projects/999/locations/us/userStores/default_user_store'

    def test_eu_location(self):
        from gam.cmd.gelicenses import _getGEParent
        assert _getGEParent('42', 'eu') == \
            'projects/42/locations/eu/userStores/default_user_store'


class TestGetLicenseConfigsParent:
    """_getLicenseConfigsParent builds the correct licenseConfigs parent."""

    def test_basic(self):
        from gam.cmd.gelicenses import _getLicenseConfigsParent
        assert _getLicenseConfigsParent('123', 'us') == \
            'projects/123/locations/us'


# ---------------------------------------------------------------------------
# _handleLROResult — pure function, tests result interpretation
# ---------------------------------------------------------------------------

class TestHandleLROResult:
    """_handleLROResult interprets LRO completion data."""

    def test_success(self, capsys):
        from gam.cmd.gelicenses import _handleLROResult
        result = _handleLROResult({'response': {}})
        assert result is True
        captured = capsys.readouterr()
        assert 'successfully' in captured.out

    def test_error_in_response(self):
        from gam.cmd.gelicenses import _handleLROResult
        data = {'error': {'message': 'quota exceeded'}}
        result = _handleLROResult(data)
        assert result is False

    def test_error_samples_in_response(self):
        from gam.cmd.gelicenses import _handleLROResult
        data = {
            'response': {
                'errorSamples': [
                    {'message': 'user not found'},
                    {'message': 'invalid email'},
                ]
            }
        }
        result = _handleLROResult(data)
        assert result is False

    def test_error_with_missing_message_uses_default(self):
        from gam.cmd.gelicenses import _handleLROResult
        data = {'error': {}}
        result = _handleLROResult(data)
        assert result is False

    def test_empty_error_samples_is_success(self, capsys):
        from gam.cmd.gelicenses import _handleLROResult
        data = {'response': {'errorSamples': []}}
        result = _handleLROResult(data)
        assert result is True


# ---------------------------------------------------------------------------
# _handleGEError — error routing
# ---------------------------------------------------------------------------

class TestHandleGEError:
    """_handleGEError routes API exceptions to the correct remediation."""

    def test_permission_denied_shows_iam_guidance(self, capsys):
        from gam.cmd.gelicenses import _handleGEError
        from gamlib import gapi as GAPI, state as GM
        GM.Globals[GM.ADMIN] = 'sa@proj.iam.gserviceaccount.com'
        with pytest.raises(SystemExit):
            _handleGEError(GAPI.permissionDenied('Access denied'), '123456')
        captured = capsys.readouterr()
        assert 'agentspaceAdmin' in captured.err
        assert 'serviceusage' not in captured.err
        assert 'enable discoveryengine' not in captured.err

    def test_forbidden_with_service_disabled(self, capsys):
        from gam.cmd.gelicenses import _handleGEError
        from gamlib import gapi as GAPI, state as GM
        GM.Globals[GM.ADMIN] = 'sa@proj.iam.gserviceaccount.com'
        with pytest.raises(SystemExit):
            _handleGEError(GAPI.forbidden('SERVICE_DISABLED: API not enabled'), '123456')
        captured = capsys.readouterr()
        assert 'enable discoveryengine.googleapis.com' in captured.err
        assert 'agentspaceAdmin' not in captured.err

    def test_forbidden_with_user_project_denied(self, capsys):
        from gam.cmd.gelicenses import _handleGEError
        from gamlib import gapi as GAPI, state as GM
        GM.Globals[GM.ADMIN] = 'sa@proj.iam.gserviceaccount.com'
        with pytest.raises(SystemExit):
            _handleGEError(GAPI.forbidden('USER_PROJECT_DENIED'), '123456')
        captured = capsys.readouterr()
        # Ambiguous error — should show both possible fixes
        assert 'enable discoveryengine.googleapis.com' in captured.err
        assert 'serviceusage.serviceUsageConsumer' in captured.err
        assert 'agentspaceAdmin' not in captured.err

    def test_not_found_exits(self):
        from gam.cmd.gelicenses import _handleGEError
        from gamlib import gapi as GAPI, state as GM
        GM.Globals[GM.ADMIN] = 'sa@proj.iam.gserviceaccount.com'
        with pytest.raises(SystemExit):
            _handleGEError(GAPI.notFound('not found'), '123456')

    def test_unknown_error_type_returns(self):
        """Unrecognized exception types are not handled — function returns."""
        from gam.cmd.gelicenses import _handleGEError
        from gamlib import state as GM
        GM.Globals[GM.ADMIN] = 'sa@proj.iam.gserviceaccount.com'
        # Should not raise — just returns
        _handleGEError(ValueError('unexpected'), '123456')


# ---------------------------------------------------------------------------
# _resolveLocation
# ---------------------------------------------------------------------------

class TestResolveLocation:
    """_resolveLocation auto-detects GE location when not provided."""

    def test_provided_location_returned_immediately(self):
        from gam.cmd.gelicenses import _resolveLocation
        result = _resolveLocation('my-project', 'eu')
        assert result == 'eu'

    @staticmethod
    def _make_probe_svc(configs):
        """Return a mock service whose licenseConfigs().list().execute() returns configs."""
        svc = MagicMock()
        svc.projects().locations().licenseConfigs().list().execute.return_value = {
            'licenseConfigs': configs
        }
        return svc

    @staticmethod
    def _make_probe_svc_error(exc):
        """Return a mock service whose licenseConfigs().list().execute() raises."""
        svc = MagicMock()
        svc.projects().locations().licenseConfigs().list().execute.side_effect = exc
        return svc

    def test_auto_selects_single_location(self, capsys):
        from gam.cmd.gelicenses import _resolveLocation
        configs = [{'name': 'projects/123/locations/global/licenseConfigs/sub-1'}]

        # global has configs, us and eu have none
        svcs = [self._make_probe_svc(configs),
                self._make_probe_svc([]),
                self._make_probe_svc([])]

        with patch('gam.cmd.gelicenses._buildGEService', side_effect=svcs):
            result = _resolveLocation('my-project', None)
        assert result == 'global'
        captured = capsys.readouterr()
        assert 'Auto-selected location: global' in captured.out

    def test_errors_on_no_locations(self):
        from gam.cmd.gelicenses import _resolveLocation

        svcs = [self._make_probe_svc([]),
                self._make_probe_svc([]),
                self._make_probe_svc([])]

        with patch('gam.cmd.gelicenses._buildGEService', side_effect=svcs):
            with pytest.raises(SystemExit):
                _resolveLocation('my-project', None)

    def test_errors_on_multiple_locations(self):
        from gam.cmd.gelicenses import _resolveLocation
        configs = [{'name': 'projects/123/locations/x/licenseConfigs/sub-1'}]

        svcs = [self._make_probe_svc(configs),
                self._make_probe_svc(configs),
                self._make_probe_svc([])]

        with patch('gam.cmd.gelicenses._buildGEService', side_effect=svcs):
            with pytest.raises(SystemExit):
                _resolveLocation('my-project', None)

    def test_skips_locations_with_errors(self, capsys):
        from gam.cmd.gelicenses import _resolveLocation
        configs_eu = [{'name': 'projects/123/locations/eu/licenseConfigs/sub-1'}]

        # global errors, us empty, eu has configs
        svcs = [self._make_probe_svc_error(Exception('wrong region')),
                self._make_probe_svc([]),
                self._make_probe_svc(configs_eu)]

        with patch('gam.cmd.gelicenses._buildGEService', side_effect=svcs):
            result = _resolveLocation('my-project', None)
        assert result == 'eu'
        captured = capsys.readouterr()
        assert 'global: not available' in captured.out


# ---------------------------------------------------------------------------
# _resolveSubscriptionId
# ---------------------------------------------------------------------------

class TestResolveSubscriptionId:
    """_resolveSubscriptionId validates or auto-discovers subscriptions."""

    def test_provided_id_matched_against_api(self):
        from gam.cmd.gelicenses import _resolveSubscriptionId
        configs = [{'name': 'projects/99999/locations/us/licenseConfigs/my-sub-id'}]
        with patch('gam.cmd.gelicenses._fetchSubscriptions', return_value=configs):
            result = _resolveSubscriptionId(MagicMock(), '123', 'us', 'my-sub-id')
        assert result == 'projects/99999/locations/us/licenseConfigs/my-sub-id'

    def test_auto_selects_single_subscription(self, capsys):
        from gam.cmd.gelicenses import _resolveSubscriptionId
        configs = [{'name': 'projects/123/locations/us/licenseConfigs/sub-abc'}]
        with patch('gam.cmd.gelicenses._fetchSubscriptions', return_value=configs):
            result = _resolveSubscriptionId(MagicMock(), '123', 'us', None)
        assert result == 'projects/123/locations/us/licenseConfigs/sub-abc'
        captured = capsys.readouterr()
        assert 'Auto-selected' in captured.out

    def test_errors_on_no_subscriptions(self):
        from gam.cmd.gelicenses import _resolveSubscriptionId
        with patch('gam.cmd.gelicenses._fetchSubscriptions', return_value=[]):
            with pytest.raises(SystemExit):
                _resolveSubscriptionId(MagicMock(), '123', 'us', None)

    def test_errors_on_multiple_subscriptions(self):
        from gam.cmd.gelicenses import _resolveSubscriptionId
        configs = [
            {'name': 'projects/123/locations/us/licenseConfigs/sub-a'},
            {'name': 'projects/123/locations/us/licenseConfigs/sub-b'},
        ]
        with patch('gam.cmd.gelicenses._fetchSubscriptions', return_value=configs):
            with pytest.raises(SystemExit):
                _resolveSubscriptionId(MagicMock(), '123', 'us', None)


# ---------------------------------------------------------------------------
# _batchUpdateLicenses — body construction
# ---------------------------------------------------------------------------

class TestBatchUpdateLicenses:
    """_batchUpdateLicenses constructs the correct API request body."""

    def test_assigns_only(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        with patch('gam.cmd.gelicenses.callGAPI', return_value={'done': True, 'response': {}}) as mock_call:
            _batchUpdateLicenses(MagicMock(), '123', 'us', 'sub-1',
                                 assigns=['alice@example.com'], removes=[], delete_record=False)
            body = mock_call.call_args[1]['body']
            assert body['deleteUnassignedUserLicenses'] is False
            licenses = body['inlineSource']['userLicenses']
            assert len(licenses) == 1
            assert licenses[0]['userPrincipal'] == 'alice@example.com'
            assert licenses[0]['licenseAssignmentState'] == 'ASSIGNED'
            assert 'sub-1' in licenses[0]['licenseConfig']

    def test_removes_only(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        with patch('gam.cmd.gelicenses.callGAPI', return_value={'done': True, 'response': {}}) as mock_call:
            _batchUpdateLicenses(MagicMock(), '123', 'us', None,
                                 assigns=[], removes=['bob@example.com'], delete_record=True)
            body = mock_call.call_args[1]['body']
            assert body['deleteUnassignedUserLicenses'] is True
            licenses = body['inlineSource']['userLicenses']
            assert len(licenses) == 1
            assert licenses[0]['userPrincipal'] == 'bob@example.com'
            assert licenses[0]['licenseAssignmentState'] == 'UNASSIGNED'

    def test_mixed_assigns_and_removes(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        with patch('gam.cmd.gelicenses.callGAPI', return_value={'done': True, 'response': {}}) as mock_call:
            _batchUpdateLicenses(MagicMock(), '123', 'us', 'sub-1',
                                 assigns=['alice@example.com'],
                                 removes=['bob@example.com'],
                                 delete_record=False)
            body = mock_call.call_args[1]['body']
            licenses = body['inlineSource']['userLicenses']
            assert len(licenses) == 2
            states = {l['userPrincipal']: l['licenseAssignmentState'] for l in licenses}
            assert states['alice@example.com'] == 'ASSIGNED'
            assert states['bob@example.com'] == 'UNASSIGNED'

    def test_empty_lists_no_api_call(self, capsys):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        with patch('gam.cmd.gelicenses.callGAPI') as mock_call:
            _batchUpdateLicenses(MagicMock(), '123', 'us', 'sub-1',
                                 assigns=[], removes=[], delete_record=False)
            mock_call.assert_not_called()
        captured = capsys.readouterr()
        assert 'No license changes' in captured.out

    def test_parent_path_correct(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        with patch('gam.cmd.gelicenses.callGAPI', return_value={'done': True, 'response': {}}) as mock_call:
            _batchUpdateLicenses(MagicMock(), '789', 'eu', 'sub-1',
                                 assigns=['x@example.com'], removes=[], delete_record=False)
            assert mock_call.call_args[1]['parent'] == \
                'projects/789/locations/eu/userStores/default_user_store'

    def test_license_config_uses_full_resource_name(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        full_name = 'projects/99999/locations/global/licenseConfigs/my-sub'
        with patch('gam.cmd.gelicenses.callGAPI', return_value={'done': True, 'response': {}}) as mock_call:
            _batchUpdateLicenses(MagicMock(), '456', 'global', full_name,
                                 assigns=['a@b.com'], removes=[], delete_record=False)
            lic = mock_call.call_args[1]['body']['inlineSource']['userLicenses'][0]
            assert lic['licenseConfig'] == full_name

    def test_update_mask_present(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        with patch('gam.cmd.gelicenses.callGAPI', return_value={'done': True, 'response': {}}) as mock_call:
            _batchUpdateLicenses(MagicMock(), '123', 'us', 'sub-1',
                                 assigns=['a@b.com'], removes=[], delete_record=False)
            mask = mock_call.call_args[1]['body']['inlineSource']['updateMask']
            assert 'userPrincipal' in mask
            assert 'licenseConfig' in mask
            assert 'licenseAssignmentState' in mask

    def test_permission_denied_handled(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses
        from gamlib import gapi as GAPI, state as GM
        GM.Globals[GM.ADMIN] = 'sa@proj.iam.gserviceaccount.com'

        with patch('gam.cmd.gelicenses.callGAPI', side_effect=GAPI.permissionDenied('denied')):
            with pytest.raises(SystemExit):
                _batchUpdateLicenses(MagicMock(), '123', 'us', 'sub-1',
                                     assigns=['a@b.com'], removes=[], delete_record=False)

    def test_multiple_assigns(self):
        from gam.cmd.gelicenses import _batchUpdateLicenses

        with patch('gam.cmd.gelicenses.callGAPI', return_value={'done': True, 'response': {}}) as mock_call:
            _batchUpdateLicenses(MagicMock(), '123', 'us', 'sub-1',
                                 assigns=['a@b.com', 'c@d.com', 'e@f.com'],
                                 removes=[], delete_record=False)
            licenses = mock_call.call_args[1]['body']['inlineSource']['userLicenses']
            assert len(licenses) == 3
            assert all(l['licenseAssignmentState'] == 'ASSIGNED' for l in licenses)


# ---------------------------------------------------------------------------
# _processLRO
# ---------------------------------------------------------------------------

class TestProcessLRO:
    """_processLRO handles immediate completion and missing operation names."""

    def test_already_done(self, capsys):
        from gam.cmd.gelicenses import _processLRO
        result = _processLRO(MagicMock(), {'done': True, 'response': {}})
        assert result is True

    def test_already_done_with_error(self):
        from gam.cmd.gelicenses import _processLRO
        result = _processLRO(MagicMock(), {'done': True, 'error': {'message': 'fail'}})
        assert result is False

    def test_no_operation_name(self):
        from gam.cmd.gelicenses import _processLRO
        result = _processLRO(MagicMock(), {'done': False})
        assert result is False

    def test_polls_until_done(self):
        from gam.cmd.gelicenses import _processLRO
        mock_service = MagicMock()
        poll_responses = [
            {'done': False},
            {'done': True, 'response': {}},
        ]
        with patch('gam.cmd.gelicenses.callGAPI', side_effect=poll_responses):
            with patch('gam.cmd.gelicenses.time.sleep'):
                result = _processLRO(mock_service,
                                     {'done': False, 'name': 'operations/op-123'})
        assert result is True

    def test_retries_on_not_found_then_succeeds(self):
        from gam.cmd.gelicenses import _processLRO
        from gamlib import gapi as GAPI
        mock_service = MagicMock()
        poll_responses = [
            GAPI.notFound('not found'),
            GAPI.notFound('not found'),
            {'done': True, 'response': {}},
        ]
        with patch('gam.cmd.gelicenses.callGAPI', side_effect=poll_responses):
            with patch('gam.cmd.gelicenses.time.sleep'):
                result = _processLRO(mock_service,
                                     {'done': False, 'name': 'operations/op-456'})
        assert result is True

    def test_gives_up_after_too_many_not_found(self):
        from gam.cmd.gelicenses import _processLRO
        from gamlib import gapi as GAPI
        mock_service = MagicMock()
        poll_responses = [GAPI.notFound('not found')] * 6
        with patch('gam.cmd.gelicenses.callGAPI', side_effect=poll_responses):
            with patch('gam.cmd.gelicenses.time.sleep'):
                result = _processLRO(mock_service,
                                     {'done': False, 'name': 'operations/op-789'})
        assert result is False


# ---------------------------------------------------------------------------
# buildGAPIObjectGE — endpoint selection
# ---------------------------------------------------------------------------

class TestBuildGAPIObjectGE:
    """buildGAPIObjectGE selects the correct regionalized endpoint."""

    _SA_INFO = {
        'client_email': 'sa@proj.iam.gserviceaccount.com',
        'client_id': '12345',
        'project_id': 'my-proj',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'type': 'service_account',
        'private_key_id': 'key1',
        'private_key': 'fake',
    }

    def _setup_mocks(self):
        """Create a mock credential chain."""
        mock_cred = MagicMock()
        mock_cred.with_scopes.return_value = mock_cred
        mock_cred.with_quota_project.return_value = mock_cred
        return mock_cred

    @patch('gam.util.api.googleapiclient.discovery.build')
    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_global_endpoint(self, mock_svc, mock_signer, mock_http,
                             mock_transport, mock_build):
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            buildGAPIObjectGE('123456', 'global')
            url = mock_build.call_args[1]['discoveryServiceUrl']
            assert url == 'https://discoveryengine.googleapis.com/$discovery/rest?version=v1'

    @patch('gam.util.api.googleapiclient.discovery.build')
    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_regional_endpoint_us(self, mock_svc, mock_signer, mock_http,
                                   mock_transport, mock_build):
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            buildGAPIObjectGE('123456', 'us')
            url = mock_build.call_args[1]['discoveryServiceUrl']
            assert url == 'https://us-discoveryengine.googleapis.com/$discovery/rest?version=v1'

    @patch('gam.util.api.googleapiclient.discovery.build')
    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_regional_endpoint_eu(self, mock_svc, mock_signer, mock_http,
                                   mock_transport, mock_build):
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            buildGAPIObjectGE('123456', 'eu')
            url = mock_build.call_args[1]['discoveryServiceUrl']
            assert url == 'https://eu-discoveryengine.googleapis.com/$discovery/rest?version=v1'

    @patch('gam.util.api.googleapiclient.discovery.build')
    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_scope_is_discoveryengine_serving_readwrite(self, mock_svc, mock_signer,
                                                 mock_http, mock_transport,
                                                 mock_build):
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None
        mock_cred = self._setup_mocks()

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=mock_cred):
            buildGAPIObjectGE('123456', 'eu')
            mock_cred.with_scopes.assert_called_once_with(
                ['https://www.googleapis.com/auth/discoveryengine.serving.readwrite']
            )

    @patch('gam.util.api.googleapiclient.discovery.build')
    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_quota_project_set(self, mock_svc, mock_signer, mock_http,
                                mock_transport, mock_build):
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None
        mock_cred = self._setup_mocks()

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=mock_cred):
            buildGAPIObjectGE('my-project-id', 'global')
            mock_cred.with_quota_project.assert_called_once_with('my-project-id')

    @patch('gam.util.api.googleapiclient.discovery.build')
    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_sets_admin_global(self, mock_svc, mock_signer, mock_http,
                                mock_transport, mock_build):
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        sa_info = self._SA_INFO.copy()
        sa_info['client_email'] = 'mysa@myproject.iam.gserviceaccount.com'
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = sa_info
        GM.Globals[GM.CACHE_DIR] = None

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            buildGAPIObjectGE('123456', 'global')
            assert GM.Globals[GM.ADMIN] == 'mysa@myproject.iam.gserviceaccount.com'

    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_http_error_403_exits_with_guidance(self, mock_svc, mock_signer,
                                                 mock_http, mock_transport):
        """When discovery.build() gets a 403, exit with actionable IAM guidance."""
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        import googleapiclient.errors
        import httplib2
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None

        http_error = googleapiclient.errors.HttpError(
            httplib2.Response({'status': '403'}),
            b'{"error": {"message": "Caller does not have required permission"}}',
        )

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            with patch('gam.util.api.googleapiclient.discovery.build',
                       side_effect=http_error):
                with pytest.raises(SystemExit):
                    buildGAPIObjectGE('123456', 'global')

    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_http_error_user_project_denied_shows_service_usage(self, mock_svc, mock_signer,
                                             mock_http, mock_transport,
                                             capsys):
        """USER_PROJECT_DENIED should show API enable and serviceUsageConsumer guidance."""
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        import googleapiclient.errors
        import httplib2
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None

        error_body = json.dumps({'error': {
            'message': 'Permission denied',
            'details': [
                {'@type': 'type.googleapis.com/google.rpc.ErrorInfo',
                 'reason': 'USER_PROJECT_DENIED'},
                {'@type': 'type.googleapis.com/google.rpc.LocalizedMessage',
                 'locale': 'en-US',
                 'message': 'Grant the serviceUsageConsumer role'},
            ]
        }}).encode()
        http_error = googleapiclient.errors.HttpError(
            httplib2.Response({'status': '403'}), error_body)

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            with patch('gam.util.api.googleapiclient.discovery.build',
                       side_effect=http_error):
                with pytest.raises(SystemExit):
                    buildGAPIObjectGE('my-proj', 'global')

        captured = capsys.readouterr()
        # USER_PROJECT_DENIED is ambiguous — show both possible fixes
        assert 'enable discoveryengine.googleapis.com' in captured.err
        assert 'serviceusage.serviceUsageConsumer' in captured.err
        assert 'agentspaceAdmin' not in captured.err

    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_http_error_service_disabled_shows_api_enable(self, mock_svc, mock_signer,
                                                          mock_http, mock_transport,
                                                          capsys):
        """SERVICE_DISABLED should show only API enable guidance."""
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        import googleapiclient.errors
        import httplib2
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None

        error_body = json.dumps({'error': {
            'message': 'API disabled',
            'details': [
                {'@type': 'type.googleapis.com/google.rpc.ErrorInfo',
                 'reason': 'SERVICE_DISABLED'},
            ]
        }}).encode()
        http_error = googleapiclient.errors.HttpError(
            httplib2.Response({'status': '403'}), error_body)

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            with patch('gam.util.api.googleapiclient.discovery.build',
                       side_effect=http_error):
                with pytest.raises(SystemExit):
                    buildGAPIObjectGE('my-proj', 'global')

        captured = capsys.readouterr()
        assert 'enable discoveryengine.googleapis.com' in captured.err
        assert 'agentspaceAdmin' not in captured.err
        assert 'serviceusage' not in captured.err

    @patch('gam.util.api.transportAuthorizedHttp')
    @patch('gam.util.api.getHttpObj')
    @patch('gam.util.api._getSigner', return_value=None)
    @patch('gam.util.api._getSvcAcctData')
    def test_http_error_generic_403_shows_iam_guidance(self, mock_svc, mock_signer,
                                                       mock_http, mock_transport,
                                                       capsys):
        """Generic 403 without specific reason shows IAM role guidance."""
        from gam.util.api import buildGAPIObjectGE
        from gamlib import state as GM
        import googleapiclient.errors
        import httplib2
        GM.Globals[GM.OAUTH2SERVICE_JSON_DATA] = self._SA_INFO.copy()
        GM.Globals[GM.CACHE_DIR] = None

        http_error = googleapiclient.errors.HttpError(
            httplib2.Response({'status': '403'}),
            b'{"error": {"message": "Access denied"}}',
        )

        with patch('google.oauth2.service_account.Credentials.from_service_account_info',
                   return_value=self._setup_mocks()):
            with patch('gam.util.api.googleapiclient.discovery.build',
                       side_effect=http_error):
                with pytest.raises(SystemExit):
                    buildGAPIObjectGE('my-proj', 'global')

        captured = capsys.readouterr()
        assert 'agentspaceAdmin' in captured.err
        assert 'serviceusage' not in captured.err


# ---------------------------------------------------------------------------
# Sync delta computation
# ---------------------------------------------------------------------------

class TestSyncDeltaComputation:
    """syncGELicense correctly computes assign/remove sets."""

    def _setup_act(self):
        """Set Act to SYNC so display functions work."""
        from gam.var import Act
        Act.Set(Act.SYNC)

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._getAllLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_sync_adds_missing_removes_extra(self, mock_projloc, mock_build,
                                              mock_resolve, mock_licenses,
                                              mock_batch):
        self._setup_act()
        from gam.cmd.gelicenses import syncGELicense
        mock_licenses.return_value = [
            {'userPrincipal': 'alice@example.com', 'licenseAssignmentState': 'ASSIGNED'},
            {'userPrincipal': 'charlie@example.com', 'licenseAssignmentState': 'ASSIGNED'},
        ]
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 2, ['alice@example.com', 'bob@example.com'])):
            syncGELicense(['alice@example.com', 'bob@example.com'])

        mock_batch.assert_called_once()
        call_kwargs = mock_batch.call_args[1]
        assert set(call_kwargs['assigns']) == {'bob@example.com'}
        assert set(call_kwargs['removes']) == {'charlie@example.com'}

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._getAllLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_sync_already_in_sync(self, mock_projloc, mock_build,
                                   mock_resolve, mock_licenses, mock_batch,
                                   capsys):
        self._setup_act()
        from gam.cmd.gelicenses import syncGELicense
        mock_licenses.return_value = [
            {'userPrincipal': 'alice@example.com', 'licenseAssignmentState': 'ASSIGNED'},
        ]
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 1, ['alice@example.com'])):
            syncGELicense(['alice@example.com'])

        mock_batch.assert_not_called()
        captured = capsys.readouterr()
        assert 'already in sync' in captured.out

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._getAllLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_sync_ignores_unassigned_licenses(self, mock_projloc, mock_build,
                                               mock_resolve, mock_licenses,
                                               mock_batch):
        self._setup_act()
        from gam.cmd.gelicenses import syncGELicense
        mock_licenses.return_value = [
            {'userPrincipal': 'alice@example.com', 'licenseAssignmentState': 'ASSIGNED'},
            {'userPrincipal': 'charlie@example.com', 'licenseAssignmentState': 'UNASSIGNED'},
        ]
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 1, ['alice@example.com'])):
            syncGELicense(['alice@example.com'])

        mock_batch.assert_not_called()

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._getAllLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_sync_all_new(self, mock_projloc, mock_build,
                           mock_resolve, mock_licenses, mock_batch):
        self._setup_act()
        from gam.cmd.gelicenses import syncGELicense
        mock_licenses.return_value = []
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 2, ['a@b.com', 'c@d.com'])):
            syncGELicense(['a@b.com', 'c@d.com'])

        call_kwargs = mock_batch.call_args[1]
        assert set(call_kwargs['assigns']) == {'a@b.com', 'c@d.com'}
        assert call_kwargs['removes'] == []

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._getAllLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_sync_all_removed(self, mock_projloc, mock_build,
                               mock_resolve, mock_licenses, mock_batch):
        self._setup_act()
        from gam.cmd.gelicenses import syncGELicense
        mock_licenses.return_value = [
            {'userPrincipal': 'a@b.com', 'licenseAssignmentState': 'ASSIGNED'},
            {'userPrincipal': 'c@d.com', 'licenseAssignmentState': 'ASSIGNED'},
        ]
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 0, [])):
            syncGELicense([])

        call_kwargs = mock_batch.call_args[1]
        assert call_kwargs['assigns'] == []
        assert set(call_kwargs['removes']) == {'a@b.com', 'c@d.com'}

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._getAllLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_sync_passes_delete_record(self, mock_projloc, mock_build,
                                        mock_resolve, mock_licenses, mock_batch):
        self._setup_act()
        from gam.cmd.gelicenses import syncGELicense
        mock_licenses.return_value = [
            {'userPrincipal': 'old@b.com', 'licenseAssignmentState': 'ASSIGNED'},
        ]
        with patch('gam.cmd.gelicenses.Cmd') as mock_cmd:
            mock_cmd.ArgumentsRemaining.side_effect = [True, False]
            mock_cmd.OB_STRING = 'String'
            with patch('gam.cmd.gelicenses.getArgument', return_value='deleterecord'):
                with patch('gam.cmd.gelicenses.getEntityArgument',
                           return_value=(0, 1, ['new@b.com'])):
                    # Need to re-patch _getProjectAndLocation since Cmd is mocked
                    syncGELicense(['new@b.com'])

        call_kwargs = mock_batch.call_args[1]
        assert call_kwargs['delete_record'] is True


# ---------------------------------------------------------------------------
# createGELicense / deleteGELicense — user-scoped wiring
# ---------------------------------------------------------------------------

class TestCreateGELicense:
    """createGELicense normalizes users and calls batch with assigns."""

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_creates_licenses_for_users(self, mock_projloc, mock_build,
                                         mock_resolve, mock_batch):
        from gam.var import Act
        Act.Set(Act.CREATE)
        from gam.cmd.gelicenses import createGELicense
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 2, ['alice@example.com', 'bob@example.com'])):
            createGELicense(['alice@example.com', 'bob@example.com'])

        mock_batch.assert_called_once()
        call_kwargs = mock_batch.call_args[1]
        assert set(call_kwargs['assigns']) == {'alice@example.com', 'bob@example.com'}
        assert call_kwargs['removes'] == []
        assert call_kwargs['delete_record'] is False

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._resolveSubscriptionId', return_value='sub-1')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_empty_user_list_no_batch(self, mock_projloc, mock_build,
                                       mock_resolve, mock_batch):
        from gam.var import Act
        Act.Set(Act.CREATE)
        from gam.cmd.gelicenses import createGELicense
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 0, [])):
            createGELicense([])
        mock_batch.assert_not_called()


class TestDeleteGELicense:
    """deleteGELicense normalizes users and calls batch with removes."""

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_deletes_licenses_for_users(self, mock_projloc, mock_build,
                                         mock_batch):
        from gam.var import Act
        Act.Set(Act.DELETE)
        from gam.cmd.gelicenses import deleteGELicense
        with patch('gam.cmd.gelicenses.getEntityArgument',
                   return_value=(0, 1, ['alice@example.com'])):
            deleteGELicense(['alice@example.com'])

        mock_batch.assert_called_once()
        call_kwargs = mock_batch.call_args[1]
        assert call_kwargs['assigns'] == []
        assert set(call_kwargs['removes']) == {'alice@example.com'}
        assert call_kwargs['subscription_id'] is None

    @patch('gam.cmd.gelicenses._batchUpdateLicenses')
    @patch('gam.cmd.gelicenses._buildGEService', return_value=MagicMock())
    @patch('gam.cmd.gelicenses._getProjectAndLocation', return_value=('123', 'us'))
    def test_delete_record_flag(self, mock_projloc, mock_build, mock_batch):
        from gam.var import Act
        Act.Set(Act.DELETE)
        from gam.cmd.gelicenses import deleteGELicense
        with patch('gam.cmd.gelicenses.Cmd') as mock_cmd:
            mock_cmd.ArgumentsRemaining.side_effect = [True, False]
            with patch('gam.cmd.gelicenses.getArgument', return_value='deleterecord'):
                with patch('gam.cmd.gelicenses.getEntityArgument',
                           return_value=(0, 1, ['bob@example.com'])):
                    deleteGELicense(['bob@example.com'])

        call_kwargs = mock_batch.call_args[1]
        assert call_kwargs['delete_record'] is True


# ---------------------------------------------------------------------------
# API constant registration
# ---------------------------------------------------------------------------

class TestAPIRegistration:
    """DISCOVERYENGINE is properly registered in the API registry."""

    def test_constant_exists(self):
        from gamlib import api as API
        assert hasattr(API, 'DISCOVERYENGINE')
        assert API.DISCOVERYENGINE == 'discoveryengine'

    def test_info_entry_exists(self):
        from gamlib import api as API
        info = API._INFO[API.DISCOVERYENGINE]
        assert info['name'] == 'Discovery Engine API'
        assert info['version'] == 'v1'
        assert info['v2discovery'] is True


# ---------------------------------------------------------------------------
# ARG constants and dispatch wiring
# ---------------------------------------------------------------------------

class TestDispatchWiring:
    """GE license ARG constants exist and are wired in dispatch tables."""

    def test_arg_constants_exist(self):
        from gam.var import Cmd
        assert Cmd.ARG_GELICENSE == 'gelicense'
        assert Cmd.ARG_GELICENSES == 'gelicenses'
        assert Cmd.ARG_GESUBSCRIPTION == 'gesubscription'
        assert Cmd.ARG_GESUBSCRIPTIONS == 'gesubscriptions'
        assert Cmd.ARG_GEUSERSTORE == 'geuserstore'

    def test_user_create_dispatch(self):
        import gam
        from gam.var import Cmd
        from gam.cmd.gelicenses import createGELicense
        assert Cmd.ARG_GELICENSE in gam.USER_ADD_CREATE_FUNCTIONS
        assert gam.USER_ADD_CREATE_FUNCTIONS[Cmd.ARG_GELICENSE] is createGELicense

    def test_user_delete_dispatch(self):
        import gam
        from gam.var import Cmd
        from gam.cmd.gelicenses import deleteGELicense
        delete_funcs = gam.USER_COMMANDS_WITH_OBJECTS['delete'][1]
        assert Cmd.ARG_GELICENSE in delete_funcs
        assert delete_funcs[Cmd.ARG_GELICENSE] is deleteGELicense

    def test_user_sync_dispatch(self):
        import gam
        from gam.var import Cmd
        from gam.cmd.gelicenses import syncGELicense
        sync_funcs = gam.USER_COMMANDS_WITH_OBJECTS['sync'][1]
        assert Cmd.ARG_GELICENSE in sync_funcs
        assert sync_funcs[Cmd.ARG_GELICENSE] is syncGELicense

    def test_admin_show_gelicenses_dispatch(self):
        import gam
        from gam.var import Cmd
        from gam.cmd.gelicenses import doPrintShowGELicenses
        show_funcs = gam.MAIN_COMMANDS_WITH_OBJECTS['show'][1]
        assert Cmd.ARG_GELICENSES in show_funcs
        assert show_funcs[Cmd.ARG_GELICENSES] is doPrintShowGELicenses

    def test_admin_print_gesubscriptions_dispatch(self):
        import gam
        from gam.var import Cmd
        from gam.cmd.gelicenses import doPrintShowGESubscriptions
        print_funcs = gam.MAIN_COMMANDS_WITH_OBJECTS['print'][1]
        assert Cmd.ARG_GESUBSCRIPTIONS in print_funcs
        assert print_funcs[Cmd.ARG_GESUBSCRIPTIONS] is doPrintShowGESubscriptions

    def test_admin_show_geuserstore_dispatch(self):
        import gam
        from gam.var import Cmd
        from gam.cmd.gelicenses import doShowGEUserStore
        show_funcs = gam.MAIN_COMMANDS_WITH_OBJECTS['show'][1]
        assert Cmd.ARG_GEUSERSTORE in show_funcs
        assert show_funcs[Cmd.ARG_GEUSERSTORE] is doShowGEUserStore

    def test_gelicense_not_in_admin_create(self):
        """Mutating commands should NOT be in admin dispatch."""
        import gam
        from gam.var import Cmd
        assert Cmd.ARG_GELICENSE not in gam.COMMANDS_MAP

    def test_gelicense_not_in_admin_sync(self):
        """Sync should be user-scoped, not admin-scoped."""
        import gam
        from gam.var import Cmd
        sync_funcs = gam.MAIN_COMMANDS_WITH_OBJECTS['sync'][1]
        assert Cmd.ARG_GELICENSES not in sync_funcs


# ---------------------------------------------------------------------------
# Message strings
# ---------------------------------------------------------------------------

class TestMessageStrings:
    """GE-specific message strings are present and well-formed."""

    def test_project_location_required(self):
        from gamlib import msgs as Msg
        msg = Msg.GE_PROJECT_LOCATION_REQUIRED.format('show', 'gelicenses')
        assert 'project' in msg
        assert 'location' in msg
        assert 'show' in msg

    def test_iam_permission_denied(self):
        from gamlib import msgs as Msg
        msg = Msg.GE_IAM_PERMISSION_DENIED.format('sa@proj.iam.gserviceaccount.com', '123456')
        assert 'sa@proj.iam.gserviceaccount.com' in msg
        assert '123456' in msg
        assert 'discoveryengine.agentspaceAdmin' in msg

    def test_api_not_enabled(self):
        from gamlib import msgs as Msg
        msg = Msg.GE_API_NOT_ENABLED.format('123456')
        assert 'discoveryengine.googleapis.com' in msg
        assert '123456' in msg

    def test_userstore_not_found(self):
        from gamlib import msgs as Msg
        msg = Msg.GE_USERSTORE_NOT_FOUND.format('123456')
        assert 'location' in msg.lower()
        assert '123456' in msg

    def test_service_usage_denied(self):
        from gamlib import msgs as Msg
        msg = Msg.GE_SERVICE_USAGE_DENIED.format('sa@proj.iam.gserviceaccount.com', '123456')
        assert 'serviceusage.serviceUsageConsumer' in msg
        assert 'sa@proj.iam.gserviceaccount.com' in msg
        assert '123456' in msg
