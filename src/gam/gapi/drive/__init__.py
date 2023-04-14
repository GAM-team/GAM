import gam


def build(user=None):
    if not user:
        user = gam._get_admin_email()
    userEmail, _ = gam.convertUIDtoEmailAddress(user)
    return (userEmail, gam.buildGAPIServiceObject('drive3', userEmail))
