class Multiplexer:
    def __init__(self):
        self.mapping = {
            "ADMIN": {
                "ADMIN": "BF_ADMIN",
                "MEMBER": None,
                "OPERATOR": "BF_OPERATOR",
                "FREE": None,
                "MARKETING": None,
            },
            "CLUB": {
                "ADMIN": "BF_MEMBER",
                "MEMBER": "BF_MEMBER",
                "OPERATOR": "BF_MEMBER",
                "FREE": "BF_FREE",
                "MARKETING": "BF_MEMBER",
            },

        }

    def is_admin(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_ADMIN", source=source)

    def is_member(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_MEMBER", source=source)

    def is_free(self, source, member_category):
        return self.check_role(member_category=member_category, role="BF_FREE", source=source)

    def check_role(self, member_category, role, source):
        if source.upper() not in self.mapping.keys():
            return False

        destination = self.mapping[source.upper()][member_category.upper()]

        if destination == role:
            return True
        else:
            return False
