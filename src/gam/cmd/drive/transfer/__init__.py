"""Transfer sub-package.

Re-exports all symbols from sub-modules for backward compatibility."""

from gam.cmd.drive.transfer.fileops import (  # noqa: F401
    DOCUMENT_FORMATS_MAP,
    GOOGLEDOC_VALID_EXTENSIONS_MAP,
    HTTP_ERROR_PATTERN,
    MICROSOFT_FORMATS_LIST,
    MIMETYPE_EXTENSION_MAP,
    NON_DOWNLOADABLE_MIMETYPES,
    OPENOFFICE_FORMATS_LIST,
    SUGGESTIONS_VIEW_MODE_CHOICE_MAP,
    TRANSFER_DRIVEFILE_ACL_ROLES_MAP,
    collectOrphans,
    deleteDriveFile,
    getDriveFile,
    getGoogleDocument,
    purgeDriveFile,
    trashDriveFile,
    untrashDriveFile,
    updateGoogleDocument,
)
from gam.cmd.drive.transfer.ownership import (  # noqa: F401
    claimOwnership,
    getPermissionIdForEmail,
    transferDrive,
    transferOwnership,
    validateUserGetPermissionId,
)
